"""Dashboard core app models."""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField

from apps.auth.models import DashboardUser as User


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


class Entity(DashboardBase):
    """Represents an operator or an aggregator in the system.

    Attributes:
    - slug (AutoSlugField): Unique slug generated from the name field.
    - name (CharField): Name of the entity, unique and maximum length of 64.
    - users (ManyToManyField): Users associated with the entity.
    - proxy_for (ManyToManyField): self-referential relationship indicating proxies.
    """

    slug = AutoSlugField(_("slug"), populate_from="name", unique=True)
    name = models.CharField(_("name"), max_length=64, unique=True)
    users = models.ManyToManyField(User, verbose_name=_("users"))
    proxy_for = models.ManyToManyField("self", verbose_name=_("proxy for"), blank=True)

    class Meta:  # noqa: D106
        verbose_name = "entity"
        verbose_name_plural = "entities"
        ordering = ["name"]

    def __str__(self):  # noqa: D105
        return self.name


class DeliveryPoint(DashboardBase):
    """Represents a delivery point for electric vehicles.

    Attributes:
    - provider_assigned_id (CharField): stores the unique identifier
    assigned by the provider for the delivery point.
    - entity (ForeignKey): linking DeliveryPoint to associated Entity.
    - is_active (BooleanField): indicating the active status of the delivery point.
    """

    provider_assigned_id = models.CharField(_("provider assigned id"), max_length=64)
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, verbose_name=_("entity")
    )
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:  # noqa: D106
        verbose_name = _("delivery point")
        verbose_name_plural = _("delivery points")
        ordering = ["provider_assigned_id"]

    def __str__(self):  # noqa: D105
        return self.provider_assigned_id
