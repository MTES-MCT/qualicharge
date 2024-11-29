"""Dashboard core admin."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import DeliveryPoint, Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """Entity admin."""

    list_display = ["name", "get_users_name", "get_proxies_for", "slug"]
    filter_horizontal = (
        "users",
        "proxy_for",
    )

    @admin.display(description=_("Users"))
    def get_users_name(self, obj):
        """Returns a comma-separated string of usernames for the given object."""
        return ", ".join(user.username for user in obj.users.all())

    @admin.display(description=_("Proxy for"))
    def get_proxies_for(self, obj):
        """Returns a comma-separated string of `proxy_for.name` for the given object."""
        return ", ".join(p.name for p in obj.proxy_for.all())


@admin.register(DeliveryPoint)
class DeliveryPointAdmin(admin.ModelAdmin):
    """Delivery point admin."""

    list_display = ["provider_assigned_id", "entity", "is_active"]
