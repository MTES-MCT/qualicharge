"""Dashboard consent app managers."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ConsentManager(models.Manager):
    """Custom consent manager."""

    def get_queryset(self):
        """Return consents with active delivery point, for the current period."""
        return (
            super()
            .get_queryset()
            .filter(
                delivery_point__is_active=True,
                start__lte=timezone.now(),
                end__gte=timezone.now(),
            )
        )


class UpcomingConsentManager(models.Manager):
    """Custom consent manager, for upcoming consents."""

    def get_queryset(self):
        """Return consents with active delivery point, for the upcoming period."""
        return (
            super()
            .get_queryset()
            .filter(
                delivery_point__is_active=True,
                start__gt=timezone.now(),
                start__lte=timezone.now()
                + timedelta(days=settings.CONSENT_UPCOMING_DAYS_LIMIT),
                end__gt=timezone.now(),
            )
        )
