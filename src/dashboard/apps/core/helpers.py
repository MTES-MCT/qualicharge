"""Dashboard core helpers."""

from datetime import datetime
from typing import Optional

from django.utils import timezone

from apps.auth.models import DashboardUser
from apps.consent.models import Consent
from apps.core.annuaire_entreprise_api.adapters import (
    CompanyAddressAdapter,
    CompanyInformationAdapter,
)
from apps.core.annuaire_entreprise_api.clients import AnnuaireDesEntreprises
from apps.core.models import DeliveryPoint, Entity, Station
from apps.core.qualicharge_api.adapters import ManageStationsAdapter
from apps.core.qualicharge_api.clients import QualiChargeApi
from apps.core.utils import siret2siren


def sync_entity_from_siret(siret: str, user: Optional[DashboardUser] = None) -> Entity:
    """Retrieve, Update or create and populate entity.

    Retrieve and populate entity data based on SIRET input.
    The function uses an external API to fetch company information and address using
    the provided SIRET number.
    If the entity does not already exist in the database, it will be created.
    Optionally associates a user with the entity.

    Arguments:
        siret (str): The SIRET number used to identify and fetch the company's
        information.
        user (Optional[User]): A user instance to be associated with the created or
        updated entity. Defaults to None.

    Returns:
        Entity: The created or updated instance of the Entity model.
    """
    siren: str = siret2siren(siret)

    ade = AnnuaireDesEntreprises()

    company_info: CompanyInformationAdapter = ade.company_details(siren)
    company_address: CompanyAddressAdapter = ade.company_address(
        company_info.siret_head_office
    )

    entity, created = Entity.objects.update_or_create(
        name=company_info.name,
        siret=siret,
        legal_form=company_info.legal_form,
        naf=company_info.naf,
        address_1=company_address.address_1,
        address_2=company_address.address_2,
        address_city=company_address.city,
        address_zip_code=company_address.zip_code,
        defaults={"name": company_info.name, "siret": siret},
    )

    if user:
        entity.users.add(user)

    return entity


def sync_from_qualicharge_api(
    entity: Entity,
) -> tuple[list[DeliveryPoint], list[Consent] | None]:
    """Synchronize delivery points from QualiCharge API for a given entity.

    This function retrieves station data from the QualiCharge API based on the
    entity's SIRET and creates delivery points and associated consents, and stations
    in the database if they do not already exist.

    Parameters:
        entity (Entity): The entity object for which delivery points need to be
        synchronized. The entity must have a valid SIRET.

    Raises:
        ValueError: If the SIRET of the provided entity is None.

    Returns:
        A list of created delivery points, and a list of their associated consents
        or None if no consents were created.
    """
    if not entity.siret:
        raise ValueError("SIRET should be defined when syncing delivery points.")

    siren: str = siret2siren(entity.siret)
    after: datetime | None = None if not entity.synced_at else entity.synced_at

    qcc = QualiChargeApi()
    stations_list = qcc.manage_stations_list(siren=siren, after=after)

    created_delivery_points, consents = _create_delivery_points_from_stations_list(
        entity, stations_list
    )
    _create_stations_from_station_list(stations_list)

    return created_delivery_points, consents


def _create_delivery_points_from_stations_list(
    entity: Entity, stations_list: list[ManageStationsAdapter]
) -> tuple[list[DeliveryPoint], list[Consent] | None]:
    """Creates delivery points and associated consents from a list of stations.

    This function processes a list of stations, extracts unique PDLs (points of
    delivery), identifies new delivery points that need to be created, and creates
    them in the database alongside their corresponding consents. Existing delivery
    points are excluded based on their provider-assigned IDs. The function then
    updates the `synced_at` timestamp of the associated entity.

    Parameters:
        entity (Entity): The entity to which the delivery points are associated.
        stations_list (list[ManageStationsAdapter]): List of station data from
            which delivery points will be created. Each item represents details of
            a station.

    Returns:
        tuple:
            A tuple containing:
            - list[DeliveryPoint]: A list of newly created delivery points.
            - list[Consent] | None: A list of associated consents if any were
              created. Returns None if no consents were created.
    """
    created_delivery_points = consents = []

    # retrieve only unique PDLs from the station list
    pdls_in_stations_list = list(
        {item.num_pdl: item for item in stations_list}.values()
    )

    # get existing delivery points
    existing_delivery_points = DeliveryPoint.objects.filter(
        provider_assigned_id__in=[pdl.num_pdl for pdl in pdls_in_stations_list]
    ).values_list("provider_assigned_id", flat=True)

    # deduce delivery points that should be created
    delivery_points_to_create = [
        DeliveryPoint(
            entity=entity,
            provider_assigned_id=pdl.num_pdl,
        )
        for pdl in pdls_in_stations_list
        if pdl.num_pdl not in existing_delivery_points
    ]

    if delivery_points_to_create:
        created_delivery_points = DeliveryPoint.objects.bulk_create(
            delivery_points_to_create
        )

        # `Signals` don't work with `bulk_create`, so we manually create the
        # associated consents.
        # (https://docs.djangoproject.com/en/5.2/ref/models/querysets/#django.db.models.query.QuerySet.abulk_create)
        consents_to_create = [
            Consent(
                delivery_point=delivery_point,
                provider_assigned_id=delivery_point.provider_assigned_id,
            )
            for delivery_point in created_delivery_points
        ]

        if consents_to_create:
            consents = Consent.objects.bulk_create(consents_to_create)

    entity.synced_at = timezone.now()
    entity.save(update_fields=["synced_at"])

    return created_delivery_points, consents


def _create_stations_from_station_list(
    stations_list: list[ManageStationsAdapter],
) -> list[Station]:
    """Create stations from station list.

    Creates new stations from a given list of station adapter objects if they do not
    already exist in the database. It ensures that each new station is associated with
    its corresponding delivery point.

    Parameters:
        stations_list (list[ManageStationsAdapter]): A list of station adapter objects
            containing information about the stations to be processed.

    Returns:
        list[Station]: A list of Station objects that have been newly created in the
            database.
    """
    created_stations = []

    # get existing stations
    existing_stations = Station.objects.filter(
        id_station_itinerance__in=[st.id_station_itinerance for st in stations_list]
    ).values_list("id_station_itinerance", flat=True)

    # Preload all necessary DeliveryPoints
    delivery_points_dict = {
        dp.provider_assigned_id: dp
        for dp in DeliveryPoint.objects.filter(
            provider_assigned_id__in=[station.num_pdl for station in stations_list]
        )
    }

    # deduce stations that should be created
    stations_to_create = [
        Station(
            id_station_itinerance=station.id_station_itinerance,
            station_name=station.nom_station,
            delivery_point=delivery_points_dict.get(station.num_pdl),
        )
        for station in stations_list
        if station.id_station_itinerance not in existing_stations
    ]

    if stations_to_create:
        created_stations = Station.objects.bulk_create(stations_to_create)

    return created_stations
