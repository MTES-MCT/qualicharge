"""Dashboard consent app views."""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Index view of the consent app."""

    template_name = "consent/index.html"

    def get_context_data(self, **kwargs):
        """Add custom context to the view."""
        context = super().get_context_data(**kwargs)
        context["breadcrumb_data"] = {
            "current": _("Consent"),
        }
        return context


class ManageView(TemplateView):
    """Consents management view."""

    template_name = "consent/consent-management.html"

    def get_context_data(self, **kwargs):
        """Add custom context to the view."""
        context = super().get_context_data(**kwargs)
        context["breadcrumb_data"] = {
            "links": [
                {"url": reverse("consent:index"), "title": _("Consent")},
            ],
            "current": _("Manage Consents"),
        }
        return context
