"""Dashboard consent admin."""

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import AWAITING, REVOKED
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
    actions = ["make_revoked", "make_awaiting"]

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

    @admin.action(description=_("Mark selected consents as awaiting"))
    def make_awaiting(self, request, queryset):
        """Mark selected consents as awaiting."""
        queryset.update(status=AWAITING, updated_at=timezone.now(), revoked_at=None)
        self.message_user(
            request,
            _("Selected consents have been marked as awaiting."),
            messages.SUCCESS,
        )
