"""Dashboard auth admin."""

import sentry_sdk
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import escape, mark_safe  # type: ignore
from django.utils.translation import gettext_lazy as _

from ..core.helpers import sync_entity_from_siret
from ..core.models import Entity
from .forms import DashboardUserForm
from .models import DashboardUser


@admin.register(DashboardUser)
class DashboardUserAdmin(UserAdmin):
    """Dashboard user admin based on UserAdmin."""

    form = DashboardUserForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (_("ProConnect"), {"fields": ("siret",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_validated",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_validated",
        "is_attached_to_entity",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "is_validated")

    def response_change(self, request, obj):
        """Synchronize the entity.

        Sync the entity with "annuaire des entreprises" API and attaches it to the user.
        """
        if "_sync_entity" in request.POST:
            try:
                entity: Entity = sync_entity_from_siret(obj.siret, obj)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                messages.error(
                    request,
                    _(f"Entity synchronization error ({obj.siret}): {str(e)}"),
                )
            else:
                entity_url = reverse("admin:qcd_core_entity_change", args=[entity.id])
                self.message_user(
                    request,
                    mark_safe(  # noqa: S308
                        _(
                            f"Entity with siret {escape(obj.siret)} has been synced. "
                            f"(Entity: <a href='{escape(entity_url)}' target='_blank'>"
                            f"{escape(entity)}</a>)."
                        )
                    ),
                    messages.SUCCESS,
                )
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def is_attached_to_entity(self, obj) -> bool:
        """Return True if the user is attached to an entity."""
        return obj.get_entities().exists()

    is_attached_to_entity.short_description = _("is attached to an Entity")  # type: ignore
    is_attached_to_entity.boolean = True  # type: ignore
