"""Dashboard consent app signals."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import DeliveryPoint

from .models import Consent


@receiver(post_save, sender=DeliveryPoint, dispatch_uid="handle_new_delivery_point")
def handle_new_delivery_point(sender, instance, created, **kwargs):
    """Signal triggered after a new DeliveryPoint is saved.

    Create a new Consent object for the delivery point.
    """
    if created:
        Consent.objects.create(
            delivery_point=instance,
            id_station_itinerance=instance.id_station_itinerance,
            station_name=instance.station_name,
            provider_assigned_id=instance.provider_assigned_id,
        )
