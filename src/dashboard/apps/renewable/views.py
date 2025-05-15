"""Dashboard renewable meter app views."""

from typing import Any

import sentry_sdk
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import AnymailMessage
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.forms import modelformset_factory
from django.shortcuts import redirect
from django.urls import reverse_lazy as reverse
from django.utils import timezone
from django.utils import timezone as django_timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView, TemplateView

from apps.core.mixins import EntityViewMixin
from apps.core.models import DeliveryPoint, Entity
from apps.core.utils import get_previous_quarter_date_range, get_quarter_number
from apps.core.views import BaseView
from apps.renewable.forms import (
    DeliveryPointRenewableForm,
    RenewableForm,
    RenewableFormSet,
)
from apps.renewable.helpers import get_opening_period_dates, is_in_opening_period
from apps.renewable.models import Renewable

BREADCRUMB_CURRENT_LABEL = _("Renewable meter")


class RestrictedPeriodView(TemplateView):
    """Redirect to the restricted period view."""

    template_name = "renewable/restricted_period.html"

    def get_context_data(self, **kwargs):
        """Add custom attributes to the context."""
        period_days = settings.RENEWABLE_OPENING_PERIOD_DAYS
        start_period, end_period = get_opening_period_dates()

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "start_period": start_period,
                "end_period": end_period,
                "period_days": period_days,
            }
        )
        return context


class IndexView(BaseView, TemplateView):
    """Index view of the renewable meter app."""

    template_name = "renewable/index.html"
    breadcrumb_current = BREADCRUMB_CURRENT_LABEL

    def get_context_data(self, **kwargs):
        """Add custom attributes to the context."""
        entities: QuerySet[Entity] = self.request.user.get_entities()

        context = super().get_context_data(**kwargs)
        context["entities"] = entities
        context["has_pending_renewable"] = any(
            entity.count_unsubmitted_quarterly_renewables() for entity in entities
        )
        context["has_submitted_renewable"] = any(
            entity.count_renewables() for entity in entities
        )
        context.update(self._get_period_related_context())

        return context

    @staticmethod
    def _get_period_related_context():
        """Return the context related to the period."""
        is_opening_period = is_in_opening_period(timezone.now().date())

        context = {"is_opening_period": is_opening_period}

        if not is_opening_period:
            start, end = get_opening_period_dates()
            start_period: str = start.strftime("%d/%m/%Y")
            end_period: str = end.strftime("%d/%m/%Y")
            context["period_message"] = _(
                f"The quarterly submission period for renewable energy readings "
                f"(<em>from {start_period} to {end_period}</em>) has ended."
            )

        return context


class RenewableMetterReadingFormView(EntityViewMixin, BaseView, FormView):
    """Manage renewable meters."""

    template_name = "renewable/manage.html"
    success_url = reverse("renewable:index")
    form_class = RenewableForm

    breadcrumb_current = _("Manage renewable meter reading")
    breadcrumb_links = [
        {"url": reverse("renewable:index"), "title": BREADCRUMB_CURRENT_LABEL},
    ]

    def dispatch(self, request, *args, **kwargs):
        """Checks access to the view based on the opening period and entity permissions.

        HttpResponse: Redirect or response from parent view.
        """
        if not self._is_access_allowed():
            return redirect("renewable:restricted_period")
        return super().dispatch(request, *args, **kwargs)

    def _is_access_allowed(self) -> bool:
        """Return if access is allowed based on time period and permissions.

        Returns:
            bool: True if access is allowed, False otherwise
        """
        now = timezone.now().date()
        entity = self.get_entity()
        return is_in_opening_period(now) or entity.can_bypass_renewable_period

    def get_context_data(self, **kwargs):
        """Add custom attributes to the context.

        - get all entities associated with the current user
        - for each entity, retrieve all quarterly renewable delivery points that
        haven't been submitted yet
        - sort and group stations alphabetically by name, then update each form in
        the formset with its corresponding stations
        """
        entity = self.get_entity()
        renewable_delivery_points = entity.get_unsubmitted_quarterly_renewables()
        sorted_dps = self._order_by_stations(renewable_delivery_points)

        formset = kwargs.get("formset")
        if formset is None:
            formset_class = self.get_formset_class()
            formset = formset_class(queryset=Renewable.objects.none())

        for form, structured_point in zip(formset.forms, sorted_dps, strict=True):
            form.delivery_point_obj = structured_point["delivery_point"]
            form.stations_grouped = structured_point["stations_grouped"]

        context = super().get_context_data(**kwargs)
        context["formset"] = formset
        context["entity"] = entity
        context["signature_location"] = settings.CONSENT_SIGNATURE_LOCATION
        context["renewable_delivery_points"] = renewable_delivery_points

        return context

    def get_formset_class(self):
        """Return the formset class.

        Important: set 'extra' to match the number of delivery points
        """
        entity = self.get_entity()
        delivery_points = entity.get_unsubmitted_quarterly_renewables()

        return modelformset_factory(
            Renewable,
            form=self.form_class,
            formset=RenewableFormSet,
            extra=len(delivery_points),
            fields=["delivery_point", "meter_reading", "collected_at"],
        )

    @staticmethod
    def _order_by_stations(delivery_points):
        """Sort and group stations alphabetically by name."""
        structured_delivery_points = [
            {"delivery_point": dp, "stations_grouped": dp.get_linked_stations()}
            for dp in delivery_points
        ]

        return sorted(
            structured_delivery_points,
            key=lambda x: (
                list(x["stations_grouped"].keys())[0].casefold()
                if x["stations_grouped"]
                else ""
            ),
        )

    def post(self, request, *args, **kwargs):
        """Handle POST requests."""
        renewables = None

        formset_class = self.get_formset_class()
        formset = formset_class(
            request.POST, queryset=Renewable.objects.none(), user=request.user
        )

        if formset.is_valid():
            try:
                renewables = formset.save()
            except ValidationError:
                self.form_invalid(formset)

            self._send_email()
            messages.success(
                request,
                _(f"{len(renewables)} renewable meter reading(s) updated."),
            )
            return self.form_valid(formset)

        return self.form_invalid(formset)

    def form_invalid(self, formset):
        """Handle invalid formset."""
        formset.non_form_errors().append(_("The form contains errors."))
        return self.render_to_response(self.get_context_data(formset=formset))

    def _send_email(self) -> None:
        """Email the user after the renewable meter reading has been submitted.

        This method constructs and sends an email using the Anymail library based on
        predefined configurations.
        It logs errors with Sentry and fails silently if API errors.
        The email contains user information and a link to go back to the dashboard.

        Raises:
            AnymailRequestsAPIError: If an error occurs while sending the email.
        """
        user = self.request.user
        email_config_name = settings.DASHBOARD_EMAIL_RENEWABLE_SUBMISSION
        email_config = settings.DASHBOARD_EMAIL_CONFIGS[email_config_name]
        template_id = email_config.get("template_id")

        now = django_timezone.now()
        start_period, end_period = get_previous_quarter_date_range(now)

        email_data = {
            user.email: {  # type: ignore[union-attr]
                "last_name": user.last_name,  # type: ignore[union-attr]
                "first_name": user.first_name,  # type: ignore[union-attr]
                "start_period": start_period.strftime("%d/%m/%Y"),
                "end_period": end_period.strftime("%d/%m/%Y"),
                "link": email_config.get("link"),
            }
        }

        email = AnymailMessage(
            to=[
                user.email,  # type: ignore[union-attr]
            ],
            template_id=template_id,
            merge_data=email_data,
        )

        try:
            email.send()
        except AnymailRequestsAPIError as e:
            # fail silently and send a sentry log
            sentry_sdk.capture_exception(e)
            return


class SubmittedRenewableView(EntityViewMixin, BaseView, ListView):
    """Submitted renewable view."""

    context_object_name = "renewables"
    template_name = "renewable/submitted.html"

    breadcrumb_current = _("Submitted renewable meter reading")
    breadcrumb_links = [
        {"url": reverse("renewable:index"), "title": BREADCRUMB_CURRENT_LABEL},
    ]

    def get_queryset(self):
        """Filter queryset to only return submitted renewables for the current user."""
        return self._order_by_quarter_stations(self.get_entity().get_renewables())

    @staticmethod
    def _order_by_quarter_stations(renewables: QuerySet) -> list[Any]:
        """Sort and group stations alphabetically by name and by revert quarter.

        Returns a sorted list of dictionaries with this structured
        data, ordered by reversed quarter period date and by the first station name in a
        case-insensitive manner.

        Args:
            renewables (QuerySet): A queryset of renewables objects.

        Returns:
            list[Any]: A sorted list of dictionaries, each containing structured data
            about the renewable and its delivery point and stations.
        """
        structured_renewables = [
            {
                **renewable.__dict__,
                "provider_assigned_id": renewable.delivery_point.provider_assigned_id,
                "stations_grouped": renewable.delivery_point.get_linked_stations(),
            }
            for renewable in renewables
        ]

        return sorted(
            structured_renewables,
            key=lambda x: (
                -x["collected_at"].year,  # reverse year
                -get_quarter_number(x["collected_at"]),  # reverse quarter
                (
                    list(x["stations_grouped"].keys())[0].casefold()
                    if x["stations_grouped"]
                    else ""
                ),
            ),
        )


class DeliveryPointRenewableFormSetView(EntityViewMixin, BaseView, FormView):
    """Manage delivery points for renewable meters.."""

    template_name = "renewable/manage_delivery_points.html"
    form_class = DeliveryPointRenewableForm

    breadcrumb_current = _("Manage renewable meter reading")
    breadcrumb_links = [
        {"url": reverse("renewable:index"), "title": BREADCRUMB_CURRENT_LABEL},
    ]

    def get_context_data(self, **kwargs):
        """Add custom attributes to the context.

        - get the entity
        - get delivery points associated with the entity that are active
        - add custom attributes to each form in the formset
        """
        entity = self.get_entity()
        delivery_points = entity.delivery_points.filter(is_active=True)

        formset = kwargs.get("formset")
        if formset is None:
            formset_class = self.get_formset_class()
            formset = formset_class(queryset=delivery_points)

        for form in formset:
            form.delivery_point_obj = form.instance
            form.stations_grouped = form.instance.get_linked_stations()

        context = super().get_context_data(**kwargs)
        context["entity"] = entity
        context["formset"] = formset
        context["delivery_points"] = delivery_points

        return context

    @staticmethod
    def get_formset_class():
        """Return the formset class."""
        return modelformset_factory(
            DeliveryPoint,
            form=DeliveryPointRenewableForm,
            extra=0,
            can_delete=False,
            fields=["has_renewable"],
        )

    def post(self, request, *args, **kwargs):
        """Handle POST requests."""
        entity = self.get_entity()
        delivery_points = entity.delivery_points.filter(is_active=True)
        formset_class = self.get_formset_class()
        formset = formset_class(request.POST, queryset=delivery_points)

        if formset.is_valid():
            formset.save()
            return self.form_valid(formset)

        return self.form_invalid(formset)

    def form_valid(self, form):
        """Handle valid formset."""
        messages.success(
            self.request, _("Delivery points have been successfully updated.")
        )
        return self.render_to_response(self.get_context_data(form=form))
