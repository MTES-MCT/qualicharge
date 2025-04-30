"""Dashboard core app models."""

from collections import defaultdict

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField

from apps.consent import AWAITING
from apps.consent.models import Consent
from apps.renewable.models import Renewable

from .abstract_models import DashboardBase
from .managers import ActiveRenewableDeliveryPointManager, DeliveryPointManager
from .utils import get_previous_quarter_date_range
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

    # contract holder information
    contract_holder_name = models.CharField(
        _("contract holder name"), max_length=150, blank=True, null=True
    )
    contract_holder_email = models.EmailField(
        _("contract holder email address"), blank=True, null=True
    )
    contract_holder_phone = models.CharField(
        _("contract holder phone number"), max_length=20, blank=True, null=True
    )
    synced_at = models.DateTimeField(
        _("Last synchronization with the API occurred at"), null=True, blank=True
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

    def get_consents(
        self, status: str | None = None, obj: models.Manager = Consent.active_objects
    ) -> QuerySet:
        """Get consents associated with this entity."""
        queryset_filters: dict = {}
        if status:
            queryset_filters["status"] = status

        return (
            obj.filter(
                delivery_point__entity=self,
                **queryset_filters,
            )
            .select_related(
                "delivery_point",
                "delivery_point__entity",
            )
            .prefetch_related("delivery_point__stations")
        )

    def count_awaiting_consents(self) -> int:
        """Counts the number of validated consents associated with a given entity."""
        return self.get_consents(AWAITING).count()

    def count_upcoming_consents(self) -> int:
        """Counts the number of upcoming consents associated with a given entity."""
        return self.get_consents(obj=Consent.upcoming_objects).count()

    def count_validated_consents(self) -> int:
        """Counts the number of validated consents associated with a given entity."""
        return self.get_consents(obj=Consent.validated_objects).count()

    def get_awaiting_consents(self) -> QuerySet:
        """Get all awaiting consents for this entity."""
        return self.get_consents(AWAITING)

    def get_upcoming_consents(self) -> QuerySet:
        """Get all upcoming consents for this entity."""
        return self.get_consents(obj=Consent.upcoming_objects)

    def get_validated_consents(self) -> QuerySet:
        """Get all validated consents for this entity."""
        return self.get_consents(obj=Consent.validated_objects).order_by(
            "-start",
            "-end",
            "delivery_point__provider_assigned_id",
        )

    def get_renewables(self) -> QuerySet[Renewable]:
        """Get all renewable for this entity."""
        return Renewable.active_objects.filter(
            delivery_point__entity=self,
        ).select_related(
            "delivery_point",
            "delivery_point__entity",
        )

    def get_unsubmitted_quarterly_renewables(self) -> QuerySet:
        """Retrieve delivery points with pending renewable, within the previous quarter.

        This method identifies renewable delivery points that have not yet been included
        in the submissions for the previous quarter to the current own.
        It does so by determining:
            - the date range for the previous quarter,
            - fetching already submitted renewable delivery points for the previous
            quarter,
            - and excluding them from the available renewable delivery points.

        Returns:
            QuerySet: A QuerySet of renewable delivery points that still need to be
            submitted.
        """
        now = timezone.now()
        quarter_start_date, quarter_end_date = get_previous_quarter_date_range(now)
        submitted_renewables = (
            self.get_renewables()
            .filter(
                collected_at__gte=quarter_start_date,
                collected_at__lte=quarter_end_date,
            )
            .values_list("delivery_point__id", flat=True)
        )

        last_meter_reading_subquery = (
            Renewable.active_objects.filter(
                delivery_point=models.OuterRef("id"),
                collected_at__lt=quarter_start_date,
            )
            .order_by("-collected_at")
            .values("meter_reading")[:1]
        )

        last_collected_at_subquery = (
            Renewable.active_objects.filter(
                delivery_point=models.OuterRef("id"),
                collected_at__lt=quarter_start_date,
            )
            .order_by("-collected_at")
            .values("collected_at")[:1]
        )

        return (
            DeliveryPoint.renewable_objects.filter(
                entity=self,
            )
            .exclude(
                id__in=submitted_renewables,
            )
            .annotate(
                last_meter_reading=models.Subquery(
                    last_meter_reading_subquery, output_field=models.FloatField()
                ),
                last_collected_at=models.Subquery(
                    last_collected_at_subquery, output_field=models.DateTimeField()
                ),
            )
            .select_related("entity")
        )


class DeliveryPoint(DashboardBase):
    """Represents a delivery point for electric vehicles.

    Attributes:
    - provider_assigned_id (CharField): stores the unique identifier
    assigned by the provider for the delivery point.
    - entity (ForeignKey): linking DeliveryPoint to associated Entity.
    - is_active (BooleanField): indicating the active status of the delivery point.
    """

    provider_assigned_id = models.CharField(
        _("provider assigned id"), max_length=64, unique=True
    )
    entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="delivery_points",
        verbose_name=_("entity"),
    )
    is_active = models.BooleanField(_("is active"), default=True)
    has_renewable = models.BooleanField(_("has renewable"), default=False)

    objects = models.Manager()
    active_objects = DeliveryPointManager()
    renewable_objects = ActiveRenewableDeliveryPointManager()

    class Meta:  # noqa: D106
        verbose_name = _("delivery point")
        verbose_name_plural = _("delivery points")
        ordering = ["provider_assigned_id"]

    def __str__(self):  # noqa: D105
        return self.provider_assigned_id

    def get_linked_stations(self) -> dict[str, list[str]] | None:
        """Retrieves linked stations grouped by their station names.

        This method queries all available stations and creates a dictionary where
        station names serve as keys, and the values are lists of corresponding station
        identifiers.

        Returns:
            dict[str, list[str]] | None: A dictionary of station names mapped to lists
            of their respective station identifiers, or None if no stations are found.
        """
        stations_grouped = defaultdict(list)
        for station in self.stations.all():
            stations_grouped[station.station_name].append(station.id_station_itinerance)

        return dict(stations_grouped)


class Station(DashboardBase):
    """Represents a station for electric vehicles."""

    id_station_itinerance = models.CharField(
        _("id station itinerance"), max_length=35, blank=True, unique=True
    )
    station_name = models.CharField(_("station name"), max_length=255, blank=True)
    delivery_point = models.ForeignKey(
        DeliveryPoint,
        on_delete=models.CASCADE,
        related_name="stations",
        verbose_name=_("delivery point"),
    )

    class Meta:  # noqa: D106
        verbose_name = _("station")
        verbose_name_plural = _("stations")
        ordering = ["station_name", "id_station_itinerance"]

    def __str__(self):  # noqa: D105
        return f"{self.station_name}: {self.id_station_itinerance}"
