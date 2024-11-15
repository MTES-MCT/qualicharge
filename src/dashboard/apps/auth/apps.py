"""Dashboard auth app base config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthConfig(AppConfig):
    """Auth app config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auth"
    label = "qcd_auth"
    verbose_name = _("Authentication")
