"""Dashboard renewable app managers."""

from django.db import models


class RenewableManager(models.Manager):
    """Custom renewable manager."""

    def get_queryset(self):
        """Return renewables with active delivery points."""
        return (
            super()
            .get_queryset()
            .filter(
                delivery_point__is_active=True,
                delivery_point__has_renewable=True,
            )
        )
