"""Dashboard consent factories."""

from datetime import timedelta

import factory
from django.utils import timezone
from factory import fuzzy

from apps.auth.factories import UserFactory
from apps.core.factories import DeliveryPointFactory

from .models import Consent


class ConsentFactory(factory.django.DjangoModelFactory):
    """Factory class for creating instances of the Consent model."""

    delivery_point = factory.SubFactory(DeliveryPointFactory)
    created_by = factory.SubFactory(UserFactory)
    start = fuzzy.FuzzyDateTime(timezone.now())
    end = factory.LazyAttribute(lambda o: o.start + timedelta(days=90))

    class Meta:  # noqa: D106
        model = Consent
