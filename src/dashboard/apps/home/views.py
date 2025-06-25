"""Dashboard home app views."""

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from apps.auth.mixins import UserValidationMixin
from apps.renewable.helpers import is_in_opening_period


class IndexView(UserValidationMixin, TemplateView):
    """Index view of the homepage."""

    template_name = "home/index.html"

    def get_context_data(self, **kwargs):  # noqa: D102
        context = super().get_context_data(**kwargs)

        entities = self.request.user.get_entities()
        has_awaiting_consent = any(
            entity.get_consents().exists() for entity in entities
        )
        has_pending_renewable = any(
            entity.count_unsubmitted_quarterly_renewables() for entity in entities
        )

        if has_awaiting_consent:
            label = _("Pending consents")
            context["consent_top_detail"] = self._top_detail_context(label)

        if has_pending_renewable and is_in_opening_period(timezone.now().date()):
            label = _("Pending meters reading")
            context["renewable_top_detail"] = self._top_detail_context(label)

        return context

    @staticmethod
    def _top_detail_context(label):
        return {
            "badges": [
                {
                    "extra_classes": "fr-badge--new",
                    "label": label,
                }
            ]
        }
