"""Dashboard consent admin."""

from django.contrib import admin

from .models import Consent


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    """Consent admin."""

    pass
