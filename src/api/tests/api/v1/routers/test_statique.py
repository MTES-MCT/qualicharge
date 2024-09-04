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
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory
from qualicharge.auth.schemas import GroupOperationalUnit, ScopesEnum, User, UserGroup
from qualicharge.conf import settings
from qualicharge.factories.static import StatiqueFactory
from qualicharge.schemas.core import (
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
    for group, operational_unit in zip(groups, selected_operational_units):
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
    assert json_response == {"detail": "Requested statique does not exist"}


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


def test_bulk_with_outbound_sizes(client_auth):
    """Test the /statique/bulk create endpoint with a single or too many entries."""
    id_pdc_itinerance = "FR911E1111ER1"
    data = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
    )
    response = client_auth.post(
        "/statique/bulk", json=[json.loads(data.model_dump_json())]
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

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
