"""Dashboard consent app base config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ConsentConfig(AppConfig):
    """Consent app config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.consent"
    label = "qcd_consent"
    verbose_name = _("Consent")

    def ready(self):
        """Register signals."""
        from .signals import handle_new_delivery_point  # noqa: F401
