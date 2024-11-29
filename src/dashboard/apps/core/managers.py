"""Dashboard core app managers."""

from django.db import models


class DeliveryPointManager(models.Manager):
    """Delivery point custom manager."""

    def active(self):
        """Return active delivery points."""
        return self.filter(is_active=True)
