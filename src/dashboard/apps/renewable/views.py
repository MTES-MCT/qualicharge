"""Dashboard renewable meter app views."""

from typing import Any

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.forms import modelformset_factory
from django.urls import reverse_lazy as reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView, TemplateView

from apps.core.mixins import EntityViewMixin
from apps.core.models import Entity
from apps.core.utils import get_quarter_number
from apps.core.views import BaseView
from apps.renewable.forms import RenewableForm, RenewableFormSet
from apps.renewable.models import Renewable

BREADCRUMB_CURRENT_LABEL = _("Renewable meter")


class IndexView(BaseView, TemplateView):
    """Index view of the renewable meter app."""

    template_name = "renewable/index.html"
    breadcrumb_current = BREADCRUMB_CURRENT_LABEL

    def get_context_data(self, **kwargs):
        """Add custom attributes to the context."""
        context = super().get_context_data(**kwargs)

        entities: QuerySet[Entity] = self.request.user.get_entities()
        context["entities"] = entities
        context["has_pending_renewable"] = any(
            entity.count_unsubmitted_quarterly_renewables() for entity in entities
        )
        context["has_submitted_renewable"] = any(
            entity.count_renewables() for entity in entities
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
