"""Tests for the QualiCharge API static router."""

import gzip
import json
from random import choice, sample
from typing import cast

import pytest
from fastapi import status
from pydantic_extra_types.coordinate import Coordinate
from sqlalchemy import Column as SAColumn
from sqlalchemy import func
from sqlalchemy_utils import refresh_materialized_view
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory
from qualicharge.auth.schemas import GroupOperationalUnit, ScopesEnum, User, UserGroup
from qualicharge.conf import settings
from qualicharge.factories.static import StatiqueFactory
from qualicharge.models.static import Statique
from qualicharge.schemas.core import (
    STATIQUE_MV_TABLE_NAME,
    OperationalUnit,
    PointDeCharge,
    Station,
)
from qualicharge.schemas.utils import pdc_to_statique, save_statique, save_statiques


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": []}),
        *[
            (True, {"is_superuser": False, "scopes": [scope]})
            for scope in ScopesEnum
            if scope != ScopesEnum.STATIC_READ
        ],
    ),
    indirect=True,
)
def test_list_with_missing_scopes(client_auth):
    """Test the /statique/ list endpoint scopes."""
    response = client_auth.get("/statique/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_for_superuser(client_auth, db_session):
    """Test the /statique/ list endpoint (superuser case)."""
    # Empty response (no statiques exist)
    response = client_auth.get("/statique/")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == {
        "limit": 10,
        "offset": 0,
        "previous": None,
        "next": None,
        "items": [],
        "size": 0,
        "total": 0,
    }

    # Create statiques
    n_statiques = 3
    statiques = StatiqueFactory.batch(n_statiques)
    save_statiques(db_session, statiques)
    refresh_materialized_view(db_session, STATIQUE_MV_TABLE_NAME)
    db_statiques = sorted(
        statiques,
        key=lambda s: s.id_pdc_itinerance,
    )
    response = client_auth.get("/statique/")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == {
        "limit": 10,
        "offset": 0,
        "previous": None,
        "next": None,
        "items": [json.loads(statique.model_dump_json()) for statique in db_statiques],
        "size": 3,
        "total": 3,
    }


@pytest.mark.parametrize(
    "client_auth",
    (
        (
            True,
            {
                "is_superuser": False,
                "email": "jane@doe.com",
                "scopes": [ScopesEnum.STATIC_READ],
            },
        ),
        (
            True,
            {
                "is_superuser": False,
                "email": "jane@doe.com",
                "scopes": [ScopesEnum.STATIC_READ, ScopesEnum.STATIC_CREATE],
            },
        ),
    ),
    indirect=True,
)
def test_list_for_user(client_auth, db_session):
    """Test the /statique/ list endpoint."""
    GroupFactory.__session__ = db_session

    # Get user requesting the server
    user = db_session.exec(select(User).where(User.email == "jane@doe.com")).one()

    # Create statiques
    n_statiques = 20
    save_statiques(db_session, StatiqueFactory.batch(n_statiques))
    refresh_materialized_view(db_session, STATIQUE_MV_TABLE_NAME)

    # Select operational units linked to stations
    operational_units = db_session.exec(
        select(OperationalUnit)
        .join_from(
            Station, OperationalUnit, Station.operational_unit_id == OperationalUnit.id
        )
        .where(Station.operational_unit_id is not None)
        .distinct()
    ).all()

    # Create groups linked to operational units and our user
    n_groups = 2
    groups = GroupFactory.create_batch_sync(n_groups)
    selected_operational_units = sample(operational_units, n_groups)
    for ou in selected_operational_units:
        db_session.refresh(ou)
    unselected_operational_units = [
        operational_unit
        for operational_unit in operational_units
        if operational_unit not in selected_operational_units
    ]
    for group, operational_unit in zip(groups, selected_operational_units, strict=True):
        db_session.add(
            GroupOperationalUnit(
                group_id=group.id, operational_unit_id=operational_unit.id
            )
        )
    # Attach one more operational unit to a group so that all user groups have one
    # operational_unit except one that should have two
    extra_operational_unit = choice(unselected_operational_units)  # noqa: S311
    selected_operational_units += [extra_operational_unit]
    db_session.add(
        GroupOperationalUnit(
            group_id=groups[0].id,
            operational_unit_id=extra_operational_unit.id,
        )
    )
    # Assign our user to created groups
    for group in groups:
        db_session.add(UserGroup(user_id=user.id, group_id=group.id))

    # Expected PDC
    selected_pdcs = db_session.exec(
        select(PointDeCharge)
        .join_from(PointDeCharge, Station, PointDeCharge.station_id == Station.id)
        .join_from(
            Station, OperationalUnit, Station.operational_unit_id == OperationalUnit.id
        )
        .where(
            cast(SAColumn, OperationalUnit.id).in_(
                ou.id for ou in selected_operational_units
            )
        )
        .order_by(PointDeCharge.id_pdc_itinerance)
    ).all()
    expected_statiques = [pdc_to_statique(pdc) for pdc in selected_pdcs]

    response = client_auth.get("/statique/")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == {
        "limit": 10,
        "offset": 0,
        "previous": None,
        "next": None,
        "items": [
            json.loads(statique.model_dump_json()) for statique in expected_statiques
        ],
        "size": len(expected_statiques),
        "total": len(expected_statiques),
    }


@pytest.mark.parametrize(
    "client_auth",
    (
        (
            True,
            {
                "is_superuser": False,
                "email": "jane@doe.com",
                "scopes": [ScopesEnum.STATIC_READ],
            },
        ),
    ),
    indirect=True,
)
def test_list_for_user_with_no_operational_units(client_auth):
    """Test the /statique/ list endpoint for a user with no assigned organization."""
    response = client_auth.get("/statique/")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == {
        "limit": 10,
        "offset": 0,
        "previous": None,
        "next": None,
        "items": [],
        "size": 0,
        "total": 0,
    }


def test_list_pagination(client_auth, db_session):
    """Test the /statique/ list endpoint results pagination."""
    n_statiques = 3
    save_statiques(db_session, StatiqueFactory.batch(n_statiques))
    refresh_materialized_view(db_session, STATIQUE_MV_TABLE_NAME)

    offset = 0
    limit = 2
    response = client_auth.get(f"/statique/?{offset=}&{limit=}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response.get("total") == n_statiques
    assert json_response.get("offset") == offset
    assert json_response.get("limit") == limit
    assert json_response.get("size") == limit
    assert json_response.get("previous") is None
    assert json_response.get("next") == "http://testserver/statique/?limit=2&offset=2"

    offset = 2
    response = client_auth.get(f"/statique/?{offset=}&{limit=}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response.get("total") == n_statiques
    assert json_response.get("offset") == offset
    assert json_response.get("limit") == limit
    assert json_response.get("size") == n_statiques - offset
    assert (
        json_response.get("previous") == "http://testserver/statique/?limit=2&offset=0"
    )
    assert json_response.get("next") is None

    # Edge-case: the last page when limit == size for the last page
    offset = 2
    limit = 1
    response = client_auth.get(f"/statique/?{offset=}&{limit=}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response.get("total") == n_statiques
    assert json_response.get("offset") == offset
    assert json_response.get("limit") == limit
    assert json_response.get("size") == n_statiques - offset
    assert (
        json_response.get("previous") == "http://testserver/statique/?limit=1&offset=1"
    )
    assert json_response.get("next") is None


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": []}),
        *[
            (True, {"is_superuser": False, "scopes": [scope]})
            for scope in ScopesEnum
            if scope != ScopesEnum.STATIC_READ
        ],
    ),
    indirect=True,
)
def test_read_with_missing_scopes(client_auth):
    """Test the /statique/{id_pdc_itinerance} list endpoint scopes."""
    id_pdc_itinerance = "FR911E1111ER1"
    response = client_auth.get(f"/statique/{id_pdc_itinerance}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_read_for_superuser(client_auth, db_session):
    """Test the /statique/{id_pdc_itinerance} endpoint (superuser case)."""
    id_pdc_itinerance = "FR911E1111ER1"
    db_statique = save_statique(
        db_session, StatiqueFactory.build(id_pdc_itinerance=id_pdc_itinerance)
    )
    refresh_materialized_view(db_session, STATIQUE_MV_TABLE_NAME)

    response = client_auth.get(f"/statique/{id_pdc_itinerance}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == json.loads(db_statique.model_dump_json())


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": [ScopesEnum.STATIC_READ]}),
        (
            True,
            {
                "is_superuser": False,
                "scopes": [ScopesEnum.STATIC_READ, ScopesEnum.STATIC_CREATE],
            },
        ),
    ),
    indirect=True,
)
def test_read_for_user(client_auth, db_session):
    """Test the /statique/{id_pdc_itinerance} endpoint."""
    GroupFactory.__session__ = db_session

    # Create statique
    id_pdc_itinerance = "FR911E1111ER1"
    db_statique = save_statique(
        db_session, StatiqueFactory.build(id_pdc_itinerance=id_pdc_itinerance)
    )
    refresh_materialized_view(db_session, STATIQUE_MV_TABLE_NAME)

    # User has no assigned operational units
    response = client_auth.get(f"/statique/{id_pdc_itinerance}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Get user requesting the server
    user = db_session.exec(select(User).where(User.email == "john@doe.com")).one()
    # link him to an operational unit
    operational_unit = db_session.exec(
        select(OperationalUnit).where(OperationalUnit.code == "FR911")
    ).one()
    GroupFactory.create_sync(users=[user], operational_units=[operational_unit])

    response = client_auth.get(f"/statique/{id_pdc_itinerance}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == json.loads(db_statique.model_dump_json())


def test_read_when_statique_does_not_exist(client_auth):
    """Test the /statique/{id_pdc_itinerance} endpoint when item does not exist."""
    id_pdc_itinerance = "FR911E1111ER1"
    response = client_auth.get(f"/statique/{id_pdc_itinerance}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response == {
        "detail": (
            "Requested statique does not exist yet. You should wait up to "
            "10 minutes for a newly created entry."
        )
    }


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": []}),
        *[
            (True, {"is_superuser": False, "scopes": [scope]})
            for scope in ScopesEnum
            if scope != ScopesEnum.STATIC_CREATE
        ],
    ),
    indirect=True,
)
def test_create_with_missing_scope(client_auth):
    """Test the /statique/ create endpoint scopes."""
    id_pdc_itinerance = "FR911E1111ER1"
    data = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
    )

    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_for_superuser(client_auth):
    """Test the /statique/ create endpoint (superuser case)."""
    id_pdc_itinerance = "FR911E1111ER1"
    data = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
    )

    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == 1
    assert json_response["items"][0] == id_pdc_itinerance


def test_create_without_optional_fields(client_auth, db_session):
    """Test the /statique/ create endpoint when optional fields are not provided."""
    id_pdc_itinerance = "FR911E1111ER1"
    data = Statique(
        **StatiqueFactory.build(
            id_pdc_itinerance=id_pdc_itinerance,
        ).model_dump(
            exclude={
                "nom_amenageur",
                "siren_amenageur",
                "contact_amenageur",
                "nom_operateur",
                "telephone_operateur",
            }
        )
    )

    # Create the Statique without optional fields
    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == 1
    assert json_response["items"][0] == id_pdc_itinerance

    # Get created Statique and check defaults
    refresh_materialized_view(db_session, STATIQUE_MV_TABLE_NAME)
    response = client_auth.get(f"/statique/{id_pdc_itinerance}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    statique = Statique(**json_response)
    assert statique.nom_amenageur == "NA"
    assert statique.siren_amenageur == "123456789"
    assert statique.contact_amenageur == "na@example.org"
    assert statique.nom_operateur == "NA"
    assert statique.telephone_operateur == "tel:+33-1-23-45-67-89"


def test_create_twice(client_auth):
    """Test the /statique/ create endpoint with the same payload twice."""
    id_pdc_itinerance = "FR911E1111ER1"
    data = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
    )

    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == 1
    assert json_response["items"][0] == id_pdc_itinerance

    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Point of charge {id_pdc_itinerance} already exists"
    }


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": [ScopesEnum.STATIC_CREATE]}),
        (
            True,
            {
                "is_superuser": False,
                "scopes": [ScopesEnum.STATIC_READ, ScopesEnum.STATIC_CREATE],
            },
        ),
    ),
    indirect=True,
)
def test_create_for_user(client_auth, db_session):
    """Test the /statique/ create endpoint."""
    GroupFactory.__session__ = db_session

    # Create statique
    id_pdc_itinerance = "FR911E1111ER1"
    data = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
    )

    # User has no assigned operational units
    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_403_FORBIDDEN

    user = db_session.exec(select(User).where(User.email == "john@doe.com")).one()
    # link him to an operational unit
    operational_unit = db_session.exec(
        select(OperationalUnit).where(OperationalUnit.code == "FR911")
    ).one()

    GroupFactory.create_sync(users=[user], operational_units=[operational_unit])
    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == 1
    assert json_response["items"][0] == id_pdc_itinerance


def test_create_for_unknown_operational_unit(client_auth, db_session):
    """Test the /statique/ create endpoint."""
    n_pdc = db_session.exec(select(func.count(PointDeCharge.id))).one()
    assert n_pdc == 0

    id_pdc_itinerance = "FRFOOE0001"
    data = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
    )

    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert (
        json_response["detail"]
        == "OperationalUnit with code FRFOO should be created first"
    )

    n_pdc = db_session.exec(select(func.count(PointDeCharge.id))).one()
    assert n_pdc == 0


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": []}),
        *[
            (True, {"is_superuser": False, "scopes": [scope]})
            for scope in ScopesEnum
            if scope != ScopesEnum.STATIC_UPDATE
        ],
    ),
    indirect=True,
)
def test_update_with_missing_scope(client_auth, db_session):
    """Test the /statique/{id_pdc_itinerance} update endpoint."""
    id_pdc_itinerance = "FR911E1111ER1"
    db_statique = save_statique(
        db_session, StatiqueFactory.build(id_pdc_itinerance=id_pdc_itinerance)
    )
    new_statique = db_statique.model_copy(
        update={"contact_oprateur": "john@doe.com"}, deep=True
    )

    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(new_statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_for_superuser(client_auth, db_session):
    """Test the /statique/{id_pdc_itinerance} update endpoint (superuser case)."""
    id_pdc_itinerance = "FR911E1111ER1"
    db_statique = save_statique(
        db_session,
        StatiqueFactory.build(
            id_pdc_itinerance=id_pdc_itinerance,
            nom_amenageur="ACME Inc.",
            nom_operateur="ACME Inc.",
            nom_enseigne="ACME Inc.",
            coordonneesXY=Coordinate(-1.0, 1.0),
            station_deux_roues=False,
            cable_t2_attache=False,
        ),
    )
    new_statique = db_statique.model_copy(
        update={
            "contact_operateur": "john@doe.com",
            "nom_amenageur": "Magma Corp.",
            "nom_operateur": "Magma Corp.",
            "nom_enseigne": "Magma Corp.",
            "coordonneesXY": Coordinate(1.0, 2.0),
            "station_deux_roues": True,
            "cable_t2_attache": True,
        },
        deep=True,
    )

    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(new_statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == json.loads(new_statique.model_dump_json())


def test_update_audits(client_auth, db_session):
    """Test the /statique/{id_pdc_itinerance} update endpoint audits (superuser case)."""
    id_pdc_itinerance = "FR911E1111ER1"
    db_statique = save_statique(
        db_session,
        StatiqueFactory.build(
            id_pdc_itinerance=id_pdc_itinerance,
            nom_amenageur="ACME Inc.",
            nom_operateur="ACME Inc.",
            nom_enseigne="ACME Inc.",
            coordonneesXY=Coordinate(-1.0, 1.0),
            station_deux_roues=False,
            cable_t2_attache=False,
        ),
    )
    station = db_session.exec(
        select(Station).where(
            Station.id_station_itinerance == db_statique.id_station_itinerance
        )
    ).one()

    assert len(station.audits) == 0

    new_statique = db_statique.model_copy(
        update={
            "contact_operateur": "john@doe.com",
            "nom_amenageur": "Magma Corp.",
            "nom_operateur": "Magma Corp.",
            "nom_enseigne": "Magma Corp.",
            "coordonneesXY": Coordinate(1.0, 2.0),
            "station_deux_roues": True,
            "cable_t2_attache": True,
        },
        deep=True,
    )

    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(new_statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_200_OK
    db_session.refresh(station)

    # Get user requesting the server
    user = db_session.exec(select(User).where(User.email == "john@doe.com")).one()

    # We expect two audits as FKs are updated in a second request (once all other models
    # have been updated).
    expected_audits = 2
    assert len(station.audits) == expected_audits
    assert station.audits[0].author_id == user.id
    assert station.audits[1].author_id == user.id


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": [ScopesEnum.STATIC_UPDATE]}),
        (
            True,
            {
                "is_superuser": False,
                "scopes": [ScopesEnum.STATIC_READ, ScopesEnum.STATIC_UPDATE],
            },
        ),
    ),
    indirect=True,
)
def test_update_for_user(client_auth, db_session):
    """Test the /statique/{id_pdc_itinerance} update endpoint."""
    GroupFactory.__session__ = db_session

    # Create statique
    id_pdc_itinerance = "FR911E1111ER1"
    db_statique = save_statique(
        db_session, StatiqueFactory.build(id_pdc_itinerance=id_pdc_itinerance)
    )
    new_statique = db_statique.model_copy(
        update={"contact_oprateur": "john@doe.com"}, deep=True
    )

    # User has no assigned operational units
    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(new_statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Get user requesting the server
    user = db_session.exec(select(User).where(User.email == "john@doe.com")).one()
    # link him to an operational unit
    operational_unit = db_session.exec(
        select(OperationalUnit).where(OperationalUnit.code == "FR911")
    ).one()
    GroupFactory.create_sync(users=[user], operational_units=[operational_unit])

    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(new_statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == json.loads(new_statique.model_dump_json())


def test_update_on_wrong_id_pdc_itinerance(client_auth):
    """Test the /statique/{id_pdc_itinerance} update endpoint with a mismatching id."""
    id_pdc_itinerance = "FR911E1111ER1"
    mismatching_id_pdc_itinerance = "FR911E1111ER2"
    statique = StatiqueFactory.build(id_pdc_itinerance=mismatching_id_pdc_itinerance)

    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    json_response = response.json()
    assert json_response == {"detail": "id_pdc_itinerance does not match request body"}


def test_update_when_statique_does_not_exist(client_auth):
    """Test the /statique/{id_pdc_itinerance} update endpoint with wrong statique."""
    id_pdc_itinerance = "FR911E1111ER1"
    statique = StatiqueFactory.build(id_pdc_itinerance=id_pdc_itinerance)

    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response == {"detail": "Statique with id_pdc_itinerance does not exist"}


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": []}),
        *[
            (True, {"is_superuser": False, "scopes": [scope]})
            for scope in ScopesEnum
            if scope != ScopesEnum.STATIC_CREATE
        ],
    ),
    indirect=True,
)
def test_bulk_with_missing_scope(client_auth):
    """Test the /statique/bulk create endpoint."""
    data = StatiqueFactory.batch(
        size=2,
    )

    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_bulk_for_superuser(client_auth):
    """Test the /statique/bulk create endpoint (superuser case)."""
    data = StatiqueFactory.batch(
        size=2,
    )

    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == len(payload)
    assert json_response["items"][0] == data[0].id_pdc_itinerance
    assert json_response["items"][1] == data[1].id_pdc_itinerance


def test_bulk_without_optional_fields(client_auth):
    """Test the /statique/bulk create endpoint when optional fields are not provided."""
    data = StatiqueFactory.batch(
        size=2,
    )

    payload = [
        json.loads(
            d.model_dump_json(
                exclude={
                    "nom_amenageur",
                    "siren_amenageur",
                    "contact_amenageur",
                    "nom_operateur",
                    "telephone_operateur",
                }
            )
        )
        for d in data
    ]
    response = client_auth.post("/statique/bulk", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == len(payload)
    assert json_response["items"][0] == data[0].id_pdc_itinerance
    assert json_response["items"][1] == data[1].id_pdc_itinerance

    # Get created Statique and check defaults
    response = client_auth.get("/statique/")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    for item in json_response["items"]:
        statique = Statique(**item)
        assert statique.nom_amenageur == "NA"
        assert statique.siren_amenageur == "123456789"
        assert statique.contact_amenageur == "na@example.org"
        assert statique.nom_operateur == "NA"
        assert statique.telephone_operateur == "tel:+33-1-23-45-67-89"


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": [ScopesEnum.STATIC_CREATE]}),
        (
            True,
            {
                "is_superuser": False,
                "scopes": [ScopesEnum.STATIC_READ, ScopesEnum.STATIC_CREATE],
            },
        ),
    ),
    indirect=True,
)
def test_bulk_for_user(client_auth, db_session):
    """Test the /statique/bulk create endpoint."""
    GroupFactory.__session__ = db_session

    data = [StatiqueFactory.build(id_pdc_itinerance=f"FR911E000{i}") for i in range(2)]
    payload = [json.loads(d.model_dump_json()) for d in data]

    # User has no assigned operational units
    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Get user requesting the server
    user = db_session.exec(select(User).where(User.email == "john@doe.com")).one()
    # link him to an operational unit
    operational_unit = db_session.exec(
        select(OperationalUnit).where(OperationalUnit.code == "FR911")
    ).one()
    GroupFactory.create_sync(users=[user], operational_units=[operational_unit])

    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == len(payload)
    assert json_response["items"][0] == data[0].id_pdc_itinerance
    assert json_response["items"][1] == data[1].id_pdc_itinerance


def test_bulk_gzipped_request(client_auth):
    """Test the /statique/bulk endpoint with gzipped content."""
    statiques = StatiqueFactory.batch(
        size=2,
    )

    payload = gzip.compress(
        f"[{','.join([s.model_dump_json() for s in statiques])}]".encode("utf-8")
    )
    response = client_auth.post(
        "/statique/bulk",
        content=payload,
        headers={
            "Content-Encoding": "gzip",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == len(statiques)
    assert json_response["items"][0] == statiques[0].id_pdc_itinerance
    assert json_response["items"][1] == statiques[1].id_pdc_itinerance


def test_bulk_for_unknown_operational_unit(client_auth, db_session):
    """Test the /statique/bulk create endpoint for unknown operational unit."""
    id_pdc_itinerance = "FRFOOP0001"
    data = StatiqueFactory.batch(
        size=2,
    )
    data += [
        StatiqueFactory.build(
            id_pdc_itinerance=id_pdc_itinerance,
        )
    ]
    data += StatiqueFactory.batch(
        size=2,
    )

    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response["detail"] == "Operational units should be created first"

    # Check created statiques (if any)
    n_stations = db_session.exec(select(func.count(Station.id))).one()
    assert n_stations == 0


def test_bulk_with_inconsistent_station_data(client_auth, db_session, monkeypatch):
    """Test the /statique/bulk create endpoint with unconsistent Station data."""
    # DEBUG mode: off
    monkeypatch.setattr(settings, "DEBUG", False)
    station1 = StatiqueFactory.build(
        id_pdc_itinerance="FR911E1111ER1", date_mise_en_service="2024-10-14"
    )
    station2 = station1.model_copy(
        update={
            "id_pdc_itinerance": "FR911E1111ER2",
            "date_mise_en_service": "2024-10-15",
        }
    )
    payload = [json.loads(d.model_dump_json()) for d in [station1, station2]]
    response = client_auth.post("/statique/bulk", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json_response = response.json()
    assert (
        json_response["detail"]
        == "Point of charge (or related entry) is not consistent"
    )

    # DEBUG mode: on
    monkeypatch.setattr(settings, "DEBUG", True)
    payload = [json.loads(d.model_dump_json()) for d in [station1, station2]]
    response = client_auth.post("/statique/bulk", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json_response = response.json()
    assert "psycopg.errors.CardinalityViolation" in json_response["detail"]

    # Check created statiques (if any)
    n_stations = db_session.exec(select(func.count(Station.id))).one()
    assert n_stations == 0


def test_bulk_with_outbound_sizes(client_auth):
    """Test the /statique/bulk create endpoint with a single or too many entries."""
    id_pdc_itinerance = "FR911E1111ER1"
    data = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
    )
    response = client_auth.post(
        "/statique/bulk", json=[json.loads(data.model_dump_json())]
    )
    assert response.status_code == status.HTTP_201_CREATED

    data = StatiqueFactory.batch(
        size=settings.API_STATIQUE_BULK_CREATE_MAX_SIZE + 1,
    )
    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_bulk_does_not_create_duplicates(client_auth, db_session):
    """Test that bulk endpoint does not create duplicates."""
    size = 2
    data = StatiqueFactory.batch(
        size=size,
    )

    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == 0
    assert db_session.exec(select(func.count(Station.id))).one() == 0

    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.json()["items"]) == size
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == size
    assert db_session.exec(select(func.count(Station.id))).one() == size

    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.json()["items"]) == size
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == size
    assert db_session.exec(select(func.count(Station.id))).one() == size


def test_bulk_update(client_auth, db_session):
    """Test that bulk endpoint updates submitted statiques."""
    size = 10
    statiques = StatiqueFactory.batch(
        size=size,
        paiement_cb=False,
    )
    save_statiques(db_session, statiques)

    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == size
    assert db_session.exec(select(func.count(Station.id))).one() == size
    assert (
        db_session.exec(
            select(PointDeCharge).where(
                PointDeCharge.id_pdc_itinerance == statiques[3].id_pdc_itinerance
            )
        )
        .one()
        .paiement_cb
        is False
    )
    assert (
        db_session.exec(
            select(PointDeCharge).where(
                PointDeCharge.id_pdc_itinerance == statiques[7].id_pdc_itinerance
            )
        )
        .one()
        .paiement_cb
        is False
    )

    # Update paiement_cb field
    statiques[3].paiement_cb = statiques[7].paiement_cb = True

    payload = [json.loads(s.model_dump_json()) for s in statiques]
    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.json()["items"]) == size
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == size
    assert db_session.exec(select(func.count(Station.id))).one() == size
    assert (
        db_session.exec(
            select(PointDeCharge).where(
                PointDeCharge.id_pdc_itinerance == statiques[3].id_pdc_itinerance
            )
        )
        .one()
        .paiement_cb
    )
    assert (
        db_session.exec(
            select(PointDeCharge).where(
                PointDeCharge.id_pdc_itinerance == statiques[7].id_pdc_itinerance
            )
        )
        .one()
        .paiement_cb
    )


def test_bulk_update_audits(client_auth, db_session):
    """Test that bulk endpoint updates audits."""
    size = 10
    statiques = StatiqueFactory.batch(
        size=size,
        paiement_cb=False,
    )
    save_statiques(db_session, statiques)

    # Update paiement_cb field
    statiques[3].paiement_cb = statiques[7].paiement_cb = True

    payload = [json.loads(s.model_dump_json()) for s in statiques]
    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    # Get user requesting the server
    user = db_session.exec(select(User).where(User.email == "john@doe.com")).one()

    # Check changes and audit
    pdc3 = db_session.exec(
        select(PointDeCharge).where(
            PointDeCharge.id_pdc_itinerance == statiques[3].id_pdc_itinerance
        )
    ).one()
    assert pdc3.paiement_cb
    assert len(pdc3.audits) == 1
    assert pdc3.audits[0].author_id == user.id

    pdc7 = db_session.exec(
        select(PointDeCharge).where(
            PointDeCharge.id_pdc_itinerance == statiques[7].id_pdc_itinerance
        )
    ).one()
    assert pdc7.paiement_cb
    assert len(pdc7.audits) == 1
    assert pdc7.audits[0].author_id == user.id

    # Check no other changes exist
    not_updated = statiques.copy()
    not_updated.pop(3)
    not_updated.pop(7)
    pdcs = db_session.exec(
        select(PointDeCharge).where(
            PointDeCharge.id_pdc_itinerance.in_(
                s.id_pdc_itinerance for s in not_updated
            )
        )
    ).all()
    for pdc in pdcs:
        assert len(pdc.audits) == 0
