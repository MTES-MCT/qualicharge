"""Dashboard consent app managers."""

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
