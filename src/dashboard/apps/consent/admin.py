"""Dashboard consent admin."""

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import REVOKED
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
        "updated_at",
    ]
    search_fields = [
        "delivery_point__provider_assigned_id",
        "delivery_point__entity__name",
    ]
    list_filter = ["status"]
    date_hierarchy = "start"
    actions = ["make_revoked"]

    def has_delete_permission(self, request, obj=None):
        """Disable delete action permission for all users."""
        return False

    @admin.action(description=_("Mark selected consents as revoked"))
    def make_revoked(self, request, queryset):
        """Mark selected consents as revoked."""
        now = timezone.now()
        queryset.update(status=REVOKED, revoked_at=now, updated_at=now)
        self.message_user(
            request,
            _("Selected consents have been marked as revoked."),
            messages.SUCCESS,
        )
