"""Dashboard renewable meter app views."""

from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

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
