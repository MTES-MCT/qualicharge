"""Dashboard renewable meter app views."""

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy as reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView, TemplateView

from apps.core.mixins import EntityMixin
from apps.core.models import DeliveryPoint
from apps.core.views import BaseView
from apps.renewable.forms import RenewableReadingForm
from apps.renewable.models import Renewable

BREADCRUMB_CURRENT_LABEL = _("Renewable meter")


class IndexView(BaseView, TemplateView):
    """Index view of the renewable meter app."""

    template_name = "renewable/index.html"
    breadcrumb_current = BREADCRUMB_CURRENT_LABEL

    def get_context_data(self, **kwargs):
        """Add custom attributes to the context."""
        context = super().get_context_data(**kwargs)
        context["entities"] = self.request.user.get_entities()

        # todo : add logic
        context["has_pending_renewable"] = True
        context["has_submitted_renewable"] = True

        return context


class RenewableMetterReadingFormView(EntityMixin, BaseView, FormView):
    """Manage renewable meters."""

    template_name = "renewable/manage.html"
    success_url = reverse("renewable:index")
    form_class = RenewableReadingForm

    breadcrumb_current = _("Manage renewable meter reading")
    breadcrumb_links = [
        {"url": reverse("renewable:index"), "title": BREADCRUMB_CURRENT_LABEL},
    ]

    def get_context_data(self, **kwargs):
        """Add custom attributes to the context."""
        entity = self.get_entity()

        context = super().get_context_data(**kwargs)
        context["entity"] = entity
        context["renewable_delivery_points"] = (
            entity.get_unsubmitted_quarterly_renewables()
        )
        context["signature_location"] = settings.CONSENT_SIGNATURE_LOCATION

        return context

    def get_form_kwargs(self):
        """Set initial data for the form."""
        kwargs = super().get_form_kwargs()

        entity = self.get_entity()
        kwargs["renewable_delivery_points"] = (
            entity.get_unsubmitted_quarterly_renewables()
        )

        return kwargs

    def form_valid(self, form) -> HttpResponse:
        """Update the renewable meter reading."""
        entity = self.get_entity()
        delivery_point_ids = entity.get_unsubmitted_quarterly_renewables()

        try:
            renewables = self._bulk_create_renewables(delivery_point_ids, form)
        except ValidationError as e:
            form.add_error(None, str(e.message))
            return self.form_invalid(form)

        messages.success(
            self.request,
            _(f"{len(renewables)} renewable meter reading(s) updated."),
        )
        return super().form_valid(form)

    def _bulk_create_renewables(
        self, delivery_points: QuerySet[DeliveryPoint], form: RenewableReadingForm
    ) -> list[Renewable]:
        """Bulk update of the renewable meter reading."""
        update_objects = [
            Renewable(
                delivery_point_id=dp.id,
                collected_at=form.cleaned_data.get(f"collected_at_{dp.id}"),  # type: ignore
                meter_reading=form.cleaned_data.get(f"meter_reading_{dp.id}"),
                created_by=self.request.user,
                signed_at=timezone.now(),
                signature_location=settings.CONSENT_SIGNATURE_LOCATION,
                has_confirmed_information_accuracy=form.cleaned_data.get(
                    "has_confirmed_information_accuracy"
                ),
            )
            for dp in delivery_points
            if form.cleaned_data.get(f"meter_reading_{dp.id}")
        ]
        for renewable in update_objects:
            renewable.full_clean()

        try:
            for renewable in update_objects:
                renewable.full_clean()
        except ValidationError as e:
            raise ValidationError(_("The form contains errors.")) from e

        return Renewable.objects.bulk_create(update_objects)


class SubmittedRenewableView(EntityMixin, BaseView, ListView):
    """Submitted renewable view."""

    context_object_name = "renewables"
    template_name = "renewable/submitted.html"

    breadcrumb_current = _("Submitted renewable meter reading")
    breadcrumb_links = [
        {"url": reverse("renewable:index"), "title": BREADCRUMB_CURRENT_LABEL},
    ]

    def get_queryset(self):
        """Filter queryset to only return submitted renewables for the current user."""
        entity = self.get_entity()
        return entity.get_renewables()
