"""Dashboard core app base config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    """Core app config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "qcd_core"
    verbose_name = _("Core")
