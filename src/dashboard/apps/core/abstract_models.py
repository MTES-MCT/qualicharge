"""Dashboard consent app models."""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DashboardBase(models.Model):
    """Abstract base model, providing common fields and functionality.

    Attributes:
    - id (UUIDField): serves as the primary key, automatically generated, not editable.
    - created_at (DateTimeField): records when the object was created, not editable by
    default.
    - updated_at (DateTimeField): records when the object was last updated, editable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(
        _("created at"), editable=False, default=timezone.now
    )
    updated_at = models.DateTimeField(_("updated at"), null=True, blank=True)

    class Meta:  # noqa: D106
        abstract = True

    def save(self, *args, **kwargs):
        """Update the updated_at timestamps."""
        self.updated_at = timezone.now()
        return super(DashboardBase, self).save(*args, **kwargs)
