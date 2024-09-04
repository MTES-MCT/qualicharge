"""QualiCharge static schemas tests."""

import re
from datetime import datetime, timedelta, timezone

import pytest
from geoalchemy2.shape import to_shape
from pydantic_extra_types.coordinate import Coordinate
from shapely.geometry import mapping
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from qualicharge.factories.static import (
    AmenageurFactory,
    EnseigneFactory,
    LocalisationFactory,
    OperateurFactory,
    OperationalUnitFactory,
    PointDeChargeFactory,
    StationFactory,
)
from qualicharge.schemas.core import Amenageur, Localisation, OperationalUnit, Station


@pytest.mark.parametrize(
    "phone_number",
    (
        "+33144276350",
        "+33.1 44 27 63 50",
        "+33 (0)1 44 27 63 50",
        "+33 1 44 27 63 50",
        "0144276350",
        "01 44 27 63 50",
        "01-44-27-63-50",
        "(01)44276350",
    ),
)
def test_operateur_phone_numbers(phone_number):
    """Test Operator schema accepted phone number formats."""
    operateur = OperateurFactory.build(telephone_operateur=phone_number)
    assert operateur.telephone_operateur == "tel:+33-1-44-27-63-50"


def test_localisation_schema_set_geometry_point_validator(db_session):
    """Test the Localisation schema `set_geometry_point` validator."""
    # Create and save a new location
    loc = Localisation(
        adresse_station="4 baker street 75000 Tatooine",
        code_insee_commune="63455",
        coordonneesXY=Coordinate(longitude=3.129447, latitude=45.700327),
    )
    db_session.add(loc)
    db_session.commit()

    # Query newly created location
    db_loc = db_session.exec(select(Localisation)).one()

    assert mapping(to_shape(db_loc.coordonneesXY)) == {
        "type": "Point",
        "coordinates": (
            3.129447,
            45.700327,
        ),
    }


def test_localisation_schema_coordonneesXY_serializer(db_session):
    """Test the Localisation schema coordonneesXY serializer."""
    # Create and save a new location
    loc = Localisation(
        adresse_station="221B Baker street, London",
        code_insee_commune="63455",
        coordonneesXY=Coordinate(longitude=-3.129447, latitude=45.700327),
    )
    assert loc.model_dump(include={"coordonneesXY"}) == {
        "coordonneesXY": "POINT(-3.129447 45.700327)",
    }

    db_session.add(loc)
    db_session.commit()

    # Query newly created location
    db_loc = db_session.exec(select(Localisation)).one()

    assert db_loc.model_dump(include={"coordonneesXY"}) == {
        "coordonneesXY": {
            "latitude": 45.700327,
            "longitude": -3.129447,
        },
    }

    # Test update case
    db_loc.coordonneesXY = Coordinate(longitude=-3.129447, latitude=-55.700327)
    assert db_loc.model_dump(include={"coordonneesXY"}) == {
        "coordonneesXY": "POINT(-3.129447 -55.700327)",
    }

    db_session.add(loc)
    db_session.commit()
    db_session.refresh(db_loc)

    assert db_loc.model_dump(include={"coordonneesXY"}) == {
        "coordonneesXY": {
            "latitude": -55.700327,
            "longitude": -3.129447,
        },
    }


def test_localisation_factory():
    """Test the localisation factory."""
    localisation = LocalisationFactory.build()
    assert localisation.coordonneesXY is not None
    assert (
        re.match(r"^POINT\(-?\d+\.\d+ -?\d+\.\d+\)$", localisation.coordonneesXY)
        is not None
    )


def test_timestamped_model_defaults(db_session):
    """Test timestamped model defaults."""
    amenageur = Amenageur(
        nom_amenageur="ACME Inc.",
        siren_amenageur="130025265",
        contact_amenageur="john.doe@acme.com",
    )

    db_session.add(amenageur)
    db_session.commit()

    # Query newly created location
    db_amenageur = db_session.exec(select(Amenageur)).one()

    now = datetime.now(timezone.utc)
    assert db_amenageur.created_at < now
    assert db_amenageur.updated_at < now
    assert db_amenageur.created_at < db_amenageur.updated_at


def test_timestamped_model_constraints(db_session):
    """Test timestamped model constraints."""
    now = datetime.now(timezone.utc)
    amenageur = Amenageur(
        nom_amenageur="ACME Inc.",
        siren_amenageur="130025265",
        contact_amenageur="john.doe@acme.com",
    )
    amenageur.updated_at = now - timedelta(hours=1)

    db_session.add(amenageur)

    with pytest.raises(
        IntegrityError,
        match=(
            'new row for relation "amenageur" violates check '
            'constraint "pre-creation-update"'
        ),
    ):
        db_session.commit()


def test_timestamped_model_constraints_composition(db_session):
    """Test timestamped model constraints composition."""
    # Create the original amenageur
    original = Amenageur(
        nom_amenageur="ACME Inc.",
        siren_amenageur="130025265",
        contact_amenageur="john.doe@acme.com",
    )
    db_session.add(original)
    db_session.commit()

    # Now try to duplicate this entry
    duplicate = Amenageur(
        nom_amenageur="ACME Inc.",
        siren_amenageur="130025265",
        contact_amenageur="john.doe@acme.com",
    )
    db_session.add(duplicate)
    with pytest.raises(
        IntegrityError,
        match="duplicate key value violates unique constraint",
    ):
        db_session.commit()


@pytest.mark.parametrize(
    "related_factory,related_field",
    [
        [AmenageurFactory, "amenageur"],
        [OperateurFactory, "operateur"],
        [EnseigneFactory, "enseigne"],
        [LocalisationFactory, "localisation"],
    ],
)
def test_relationships_for_stations(db_session, related_factory, related_field):
    """Test Schema.stations one-to-many relationship.

    Note that the OperationalUnit FK is tested separately as operational units already
    exist in database and the FK is automatically set via a dedicated event listener.
    """
    related_factory.__session__ = db_session
    StationFactory.__session__ = db_session

    related = related_factory.create_sync()
    assert related.id is not None

    size = 2
    stations = StationFactory.create_batch_sync(
        size, **{f"{related_field}_id": related.id}
    )
    assert len(related.stations) == size
    assert (
        getattr(stations[0], related_field).id
        == getattr(stations[1], related_field).id
        == related.id
    )


def test_relationships_for_point_de_charge(db_session):
    """Test PointDeCharge-Station many-to-one relationship."""
    PointDeChargeFactory.__session__ = db_session
    StationFactory.__session__ = db_session

    station = StationFactory.create_sync()
    size = 10
    points_de_charge = PointDeChargeFactory.create_batch_sync(
        size, station_id=station.id
    )
    assert len(station.points_de_charge) == size
    assert all(pdc.station_id == station.id for pdc in points_de_charge)


def test_station_events(db_session):
    """Test Station events."""
    StationFactory.__session__ = db_session
    OperationalUnitFactory.__session__ = db_session

    # Create random stations
    StationFactory.create_batch_sync(5)

    # The operation unit
    operational_unit_code = "FRS63"
    operational_unit = db_session.exec(
        select(OperationalUnit).where(OperationalUnit.code == operational_unit_code)
    ).one()
    assert len(operational_unit.stations) == 0

    # Create stations that are supposed to be automatically linked
    n_stations = 3
    station = StationFactory.create_sync(
        id_station_itinerance=f"{operational_unit_code}P0001"
    )
    StationFactory.create_sync(id_station_itinerance=f"{operational_unit_code}P0002")
    StationFactory.create_sync(id_station_itinerance=f"{operational_unit_code}P0003")
    assert len(operational_unit.stations) == n_stations

    # Another operation unit
    other_operational_unit_code = "FRS72"
    other_operational_unit = db_session.exec(
        select(OperationalUnit).where(
            OperationalUnit.code == other_operational_unit_code
        )
    ).one()
    assert len(other_operational_unit.stations) == 0

    # Update station id_station_itinerance
    station.id_station_itinerance = f"{other_operational_unit_code}P0001"
    db_session.add(station)
    db_session.commit()
    assert len(other_operational_unit.stations) == 1
    assert other_operational_unit.stations[0] == station


def test_operational_unit_create_stations_fk_no_station(db_session):
    """Test OperationalUnit.create_stations_fk method with no matching station."""
    OperationalUnitFactory.__session__ = db_session

    operational_unit_code = "FRFOO"
    operational_unit = OperationalUnitFactory.create_sync(code=operational_unit_code)

    operational_unit.create_stations_fk(db_session)
    assert operational_unit.stations == []


def test_operational_unit_create_stations_fk(db_session):
    """Test OperationalUnit.create_stations_fk method."""
    StationFactory.__session__ = db_session
    OperationalUnitFactory.__session__ = db_session

    # Create random stations
    StationFactory.create_batch_sync(5)

    # The operation unit
    operational_unit_code = "FRFOO"
    operational_unit = OperationalUnitFactory.create_sync(code=operational_unit_code)

    # Create stations we want to link to the operational unit
    n_stations = 3
    for idx in range(n_stations):
        StationFactory.create_sync(
            id_station_itinerance=f"{operational_unit_code}P{idx:04d}"
        )
    operational_unit.create_stations_fk(db_session)

    # We expect to select 3 linked stations
    stations = db_session.exec(
        select(Station).where(Station.operational_unit_id == operational_unit.id)
    ).all()
    assert len(stations) == n_stations

    # Create new stations and iterate
    extra_stations = 2
    for idx in range(n_stations, n_stations + extra_stations):
        StationFactory.create_sync(
            id_station_itinerance=f"{operational_unit_code}P{idx:04d}"
        )
    operational_unit.create_stations_fk(db_session)

    # We expect to select 5 linked stations
    stations = db_session.exec(
        select(Station).where(Station.operational_unit_id == operational_unit.id)
    ).all()
    assert len(stations) == n_stations + extra_stations
