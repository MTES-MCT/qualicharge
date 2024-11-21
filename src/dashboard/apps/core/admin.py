"""Dashboard core admin."""

from django.contrib import admin

from .models import DeliveryPoint, Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """Entity admin."""

    pass


@admin.register(DeliveryPoint)
class DeliveryPointAdmin(admin.ModelAdmin):
    """Delivery point admin."""

    pass
