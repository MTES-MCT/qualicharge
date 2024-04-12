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
    PointDeChargeFactory,
    StationFactory,
)
from qualicharge.schemas.static import Amenageur, Localisation


def test_localisation_schema_set_geometry_point_validator(db_session):
    """Test the Localisation schema `set_geometry_point` validator."""
    # Create and save a new location
    loc = Localisation(
        adresse_station="4 baker street 75000 Tatooine",
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
    """Test the Localisation schema `serialize_wkb_point` serializer."""
    # Create and save a new location
    loc = Localisation(
        adresse_station="4 baker street 75000 Tatooine",
        coordonneesXY=Coordinate(longitude=3.129447, latitude=45.700327),
    )
    db_session.add(loc)
    db_session.commit()

    # Query newly created location
    db_loc = db_session.exec(select(Localisation)).one()

    assert db_loc.model_dump(include={"adresse_station", "coordonneesXY"}) == {
        "adresse_station": "4 baker street 75000 Tatooine",
        "coordonneesXY": {"latitude": 45.700327, "longitude": 3.129447},
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
    """Test Schema.stations one-to-many relationship."""
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
