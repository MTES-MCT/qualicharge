"""Dashboard consent factories."""

import factory

from apps.auth.factories import UserFactory
from apps.core.factories import DeliveryPointFactory

from .models import Consent


class ConsentFactory(factory.django.DjangoModelFactory):
    """Factory class for creating instances of the Consent model."""

    delivery_point = factory.SubFactory(DeliveryPointFactory)
    created_by = factory.SubFactory(UserFactory)

    class Meta:  # noqa: D106
        model = Consent
