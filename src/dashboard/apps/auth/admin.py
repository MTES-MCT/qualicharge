"""Dashboard auth admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import DashboardUser


@admin.register(DashboardUser)
class DashboardUserAdmin(UserAdmin):
    """Dashboard user admin based on UserAdmin."""

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

    def is_attached_to_entity(self, obj) -> bool:
        """Return True if the user is attached to an entity."""
        return obj.get_entities().exists()

    is_attached_to_entity.short_description = _("is attached to an Entity")  # type: ignore
    is_attached_to_entity.boolean = True  # type: ignore
