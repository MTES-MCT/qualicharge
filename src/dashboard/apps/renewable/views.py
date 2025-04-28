"""Dashboard renewable meter app views."""

from django.conf import settings
from django.urls import reverse_lazy as reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from apps.core.mixins import EntityMixin
from apps.core.views import BaseView

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


class RenewableMetterReadingFormView(EntityMixin, BaseView, TemplateView):
    """Manage renewable meters."""

    template_name = "renewable/manage.html"
    success_url = reverse("renewable:index")

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
