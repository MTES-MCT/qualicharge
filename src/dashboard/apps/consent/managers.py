"""Dashboard consent app managers."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.consent import AWAITING, VALIDATED


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
        """Return awaiting consents with active delivery point, for the upcoming period.

        Upcoming consents are consents that
        - start in the future and before the upcoming days limit and end in the next
        (ie: between now and 30 days from now),
        - end in the future,
        - have an active delivery point,
        - are awaiting validation,
        """
        return (
            super()
            .get_queryset()
            .filter(
                delivery_point__is_active=True,
                start__gt=timezone.now(),
                start__lte=timezone.now()
                + timedelta(days=settings.CONSENT_UPCOMING_DAYS_LIMIT),
                end__gt=timezone.now(),
                status=AWAITING,
            )
        )


class ValidatedConsentManager(models.Manager):
    """Custom consent manager, for validated consents."""

    def get_queryset(self):
        """Return validated consents with active delivery point.

        Includes validated consents for the current period and the upcoming period.
        """
        return (
            super()
            .get_queryset()
            .filter(
                Q(
                    delivery_point__is_active=True,
                    start__lte=timezone.now(),
                    end__gte=timezone.now(),
                    status=VALIDATED,
                )
                | Q(
                    delivery_point__is_active=True,
                    start__gt=timezone.now(),
                    start__lte=timezone.now()
                    + timedelta(days=settings.CONSENT_UPCOMING_DAYS_LIMIT),
                    end__gt=timezone.now(),
                    status=VALIDATED,
                )
            )
        )
