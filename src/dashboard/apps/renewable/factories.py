"""Dashboard renewable factories."""

import random

import factory
from django.utils import timezone

from apps.core.factories import DeliveryPointFactory

from .models import Renewable


class RenewableFactory(factory.django.DjangoModelFactory):
    """Factory class for creating instances of the Renewable model."""

    delivery_point = factory.SubFactory(DeliveryPointFactory)
    meter_reading = factory.LazyFunction(
        lambda: random.uniform(0.0, 9999.9)  # noqa: S311
    )
    created_by = factory.LazyAttribute(
        lambda obj: obj.delivery_point.entity.users.first()
    )
    signed_at = timezone.now()
    signature_location = "Paris"

    class Meta:  # noqa: D106
        model = Renewable
