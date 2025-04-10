"""Dashboard renewable app base config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RenewableConfig(AppConfig):
    """Renewable app config."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.renewable"
    label = "qcd_renewable"
    verbose_name = _("Renewable")
