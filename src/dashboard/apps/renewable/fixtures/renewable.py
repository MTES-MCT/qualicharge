"""Dashboard renewable dev fixture."""

import factory
from django.db import DatabaseError

from apps.core.models import DeliveryPoint

from ..factories import RenewableFactory


def seed_renewable():
    """Creates development fixtures for renewable management system."""
    if not DeliveryPoint.objects.exists():
        raise DatabaseError("We expect delivery points, run seed consents first.")

    # create renewables with meter reading in 1st quarter of 2024
    dps = DeliveryPoint.objects.all()

    RenewableFactory.create_batch(
        size=dps.count(),
        delivery_point=factory.Iterator(dps),
        collected_at="2024-01-01",
    )
