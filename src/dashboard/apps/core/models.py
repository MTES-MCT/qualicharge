"""Dashboard core app models."""

from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField

from apps.consent import AWAITING, VALIDATED
from apps.consent.models import Consent

from .abstract_models import DashboardBase
from .managers import DeliveryPointManager
from .validators import validate_naf_code, validate_siret, validate_zip_code


class Entity(DashboardBase):
    """Represents an operator or an aggregator in the system.

    Attributes:
    - slug (AutoSlugField): Unique slug generated from the name field.
    - name (CharField): Name of the entity, unique and maximum length of 64.
    - users (ManyToManyField): Users associated with the entity.
    - proxy_for (ManyToManyField): self-referential relationship indicating proxies.
    """

    ENTERPRISE: str = "ENTERPRISE"
    LOCAL_COLLECTIVITY: str = "LOCAL_COLLECTIVITY"
    EPCI: str = "EPCI"
    ASSOCIATION: str = "ASSOCIATION"

    # Used for the consent contract. Terms must be kept in French.
    COMPANY_TYPE_CHOICE = [
        (ENTERPRISE, "Entreprise"),
        (LOCAL_COLLECTIVITY, "Collectivité locale"),
        (EPCI, "EPCI"),
        (ASSOCIATION, "Association, copropriété, ..."),
    ]

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
    company_type = models.CharField(
        _("type"), max_length=50, choices=COMPANY_TYPE_CHOICE, default=ENTERPRISE
    )
    legal_form = models.CharField(
        _("legal form"),
        max_length=50,
        help_text=_("SA, SARL …"),
        blank=True,
        null=True,
    )
    trade_name = models.CharField(
        _("trade name"), max_length=255, blank=True, null=True
    )
    siret = models.CharField(
        _("SIRET"),
        max_length=14,
        validators=[validate_siret],
        blank=True,
        null=True,
    )
    naf = models.CharField(
        _("NAF code"),
        validators=[validate_naf_code],
        max_length=5,
        blank=True,
        null=True,
    )
    address_1 = models.CharField(_("address"), max_length=255, blank=True, null=True)
    address_2 = models.CharField(
        _("address complement"), max_length=255, blank=True, null=True
    )
    address_zip_code = models.CharField(
        _("zip code"),
        max_length=5,
        validators=[validate_zip_code],
        blank=True,
        null=True,
    )
    address_city = models.CharField(_("city"), max_length=255, blank=True, null=True)

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

    def get_validated_consents(self) -> QuerySet:
        """Get all awaiting consents for this entity."""
        return self.get_consents(VALIDATED)


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
