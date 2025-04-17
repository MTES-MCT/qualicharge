"""Dashboard core app managers."""

from django.db import models


class DeliveryPointManager(models.Manager):
    """Delivery point custom manager."""

    def active(self):
        """Return active delivery points."""
        return self.filter(is_active=True)


class ActiveRenewableDeliveryPointManager(models.Manager):
    """Renewable delivery point custom manager."""

    def get_queryset(self):
        """Return active delivery points with renewable."""
        return (
            super()
            .get_queryset()
            .filter(
                is_active=True,
                has_renewable=True,
            )
        )
