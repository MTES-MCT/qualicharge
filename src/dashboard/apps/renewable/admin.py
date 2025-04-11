"""Dashboard renewable admin."""

from django.contrib import admin

from .models import Renewable


@admin.register(Renewable)
class RenewableAdmin(admin.ModelAdmin):
    """Renewable admin."""

    list_display = [
        "delivery_point__provider_assigned_id",
        "delivery_point__entity__name",
        "meter_reading",
        "collected_at",
    ]
    search_fields = [
        "delivery_point__provider_assigned_id",
        "delivery_point__entity__name",
    ]
    date_hierarchy = "collected_at"
