"""Dashboard renewable dev fixture."""
import random

from apps.core.factories import DeliveryPointFactory, StationFactory
from apps.core.models import DeliveryPoint

from ..factories import RenewableFactory


def seed_renewable():
    """Creates development fixtures for renewable management system."""
    if not DeliveryPoint.objects.exists():
        size = 4
        DeliveryPointFactory.create_batch(size)

        # create stations for delivery points
        for dl in DeliveryPoint.objects.all():
            size = random.randint(1, 3)  # noqa: S311
            StationFactory.create_batch(size, delivery_point=dl)

    # create renewables with empty meter reading
    for dl in DeliveryPoint.objects.all():
        RenewableFactory(delivery_point=dl)
