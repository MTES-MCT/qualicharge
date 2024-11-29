"""Dashboard core app models."""

from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField

from apps.consent import AWAITING, VALIDATED
from apps.consent.models import Consent

from .abstract_models import DashboardBase
from .managers import DeliveryPointManager


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
    users = models.ManyToManyField(
        "qcd_auth.DashboardUser", verbose_name=_("users"), related_name="entities"
    )
    proxy_for = models.ManyToManyField(
        "self",
        verbose_name=_("proxy for"),
        blank=True,
        symmetrical=False,
        related_name="proxies",
    )

    class Meta:  # noqa: D106
        verbose_name = "entity"
        verbose_name_plural = "entities"
        ordering = ["name"]

    def __str__(self):  # noqa: D105
        return self.name

    def is_proxy_for(self) -> bool:
        """Return True if the entity is a proxy of other entities, False otherwise."""
        return self.proxy_for.exists()

    def get_proxy_entities(self) -> QuerySet:
        """Retrieve entities for which this entity is a proxy."""
        return self.proxy_for.all()

    def get_consents(self, status: str | None = None) -> QuerySet:
        """Get consents associated with this entity."""
        queryset_filters: dict = {}
        if status:
            queryset_filters["status"] = status

        return (
            Consent.active_objects.filter(
                delivery_point__entity=self,
                **queryset_filters,
            )
            .select_related(
                "delivery_point",
                "delivery_point__entity",
            )
            .order_by("delivery_point__provider_assigned_id", "start")
        )

    def count_validated_consents(self) -> int:
        """Counts the number of validated consents associated with a given entity."""
        return self.get_consents(VALIDATED).count()

    def count_awaiting_consents(self) -> int:
        """Counts the number of validated consents associated with a given entity."""
        return self.get_consents(AWAITING).count()

    def get_awaiting_consents(self) -> QuerySet:
        """Get all awaiting consents for this entity."""
        return self.get_consents(AWAITING)


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
        Entity,
        on_delete=models.CASCADE,
        related_name="delivery_points",
        verbose_name=_("entity"),
    )
    is_active = models.BooleanField(_("is active"), default=True)

    active_objects = DeliveryPointManager()
    objects = models.Manager()

    class Meta:  # noqa: D106
        verbose_name = _("delivery point")
        verbose_name_plural = _("delivery points")
        ordering = ["provider_assigned_id"]

    def __str__(self):  # noqa: D105
        return self.provider_assigned_id
