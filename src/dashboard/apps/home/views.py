"""Dashboard home app views."""

from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Index view of the homepage."""

    template_name = "home/index.html"

    def get_context_data(self, **kwargs):  # noqa: D102
        context = super().get_context_data(**kwargs)

        entities = self.request.user.get_entities()
        has_awaiting_consent = any(entity.get_consents for entity in entities)

        if has_awaiting_consent:
            context["top_detail"] = {
                "badges": [
                    {
                        "extra_classes": "fr-badge--new",
                        "label": _("Pending consents"),
                    }
                ]
            }

        return context
