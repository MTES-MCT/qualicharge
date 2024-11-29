"""Dashboard consent admin."""

from django.contrib import admin

from .models import Consent


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    """Consent admin."""

    list_display = [
        "delivery_point__provider_assigned_id",
        "delivery_point__entity__name",
        "status",
        "start",
        "end",
        "revoked_at",
    ]
    search_fields = [
        "delivery_point__provider_assigned_id",
        "delivery_point__entity__name",
    ]
    list_filter = ["status"]
    date_hierarchy = "start"
