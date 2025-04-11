"""Dashboard renewable factories."""

import factory

from apps.auth.factories import UserFactory
from apps.core.factories import DeliveryPointFactory

from .models import Renewable


class RenewableFactory(factory.django.DjangoModelFactory):
    """Factory class for creating instances of the Renewable model."""

    delivery_point = factory.SubFactory(DeliveryPointFactory)
    created_by = factory.SubFactory(UserFactory)
    provider_assigned_id = factory.LazyAttribute(
        lambda obj: obj.delivery_point.provider_assigned_id
    )

    class Meta:  # noqa: D106
        model = Renewable
