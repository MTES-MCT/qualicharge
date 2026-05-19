"""Tests for the QualiCharge API tariff router."""

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

import pytest
from fastapi import status
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory
from qualicharge.auth.schemas import GroupOperationalUnit, ScopesEnum, User
from qualicharge.factories.static import StatiqueFactory
from qualicharge.factories.tariff import TariffCreateFactory, TariffObjectFactory
from qualicharge.schemas.core import OperationalUnit, PointDeCharge
from qualicharge.schemas.tariff import PointDeChargeTariff, Tariff
from qualicharge.schemas.utils import save_statiques


def _tariff_payload(id_: str, start: datetime, end: datetime, pdcs: list[str]) -> dict:
    """Build a tariff creation payload."""
    raw = TariffObjectFactory.build(
        tariff_id=id_,
        last_updated=start,
        start_date_time=start,
        end_date_time=end,
    )
    return TariffCreateFactory.build(
        tariff=raw,
        targets=pdcs,
    ).model_dump(by_alias=True, mode="json")


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": []}),
        *[
            (True, {"is_superuser": False, "scopes": [scope]})
            for scope in ScopesEnum
            if scope
            not in {
                ScopesEnum.TARIFF_CREATE,
                ScopesEnum.TARIFF_READ,
                ScopesEnum.TARIFF_UPDATE,
                ScopesEnum.TARIFF_DELETE,
            }
        ],
    ),
    indirect=True,
)
def test_tariff_api_missing_scopes(client_auth):
    """Test tariff endpoints scopes."""
    tariff_id = uuid4()

    assert client_auth.get("/statique/tariff/").status_code == status.HTTP_403_FORBIDDEN
    assert (
        client_auth.post("/statique/tariff/", json={}).status_code
        == status.HTTP_403_FORBIDDEN
    )
    assert (
        client_auth.get(f"/statique/tariff/{tariff_id}").status_code
        == status.HTTP_403_FORBIDDEN
    )
    assert (
        client_auth.put(f"/statique/FRS63E0001/tariff/{tariff_id}").status_code
        == status.HTTP_403_FORBIDDEN
    )


def test_tariff_api_workflow(db_session, client_auth):
    """Test tariff creation, reads, association and soft-deletion."""
    n_pdcs = 2
    save_statiques(db_session, StatiqueFactory.batch(n_pdcs))
    pdcs = db_session.exec(select(PointDeCharge)).all()
    assert len(pdcs) == n_pdcs

    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    payload = _tariff_payload("tariff-1", start, end, [pdcs[0].id_pdc_itinerance])

    response = client_auth.post("/statique/tariff/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    created = response.json()
    tariff_id = UUID(created["id"])
    assert created["original_id"] == "tariff-1"
    assert created["id_pdc_itinerance"] == [pdcs[0].id_pdc_itinerance]

    db_tariff = db_session.get(Tariff, tariff_id)
    assert db_tariff is not None
    assert db_tariff.deleted_at is None

    response = client_auth.get("/statique/tariff/")
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [str(tariff_id)]

    response = client_auth.get(f"/statique/tariff/{tariff_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(tariff_id)

    response = client_auth.get(
        f"/statique/{pdcs[0].id_pdc_itinerance}/tariff",
        params={"at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(tariff_id)

    response = client_auth.get(
        f"/statique/{pdcs[1].id_pdc_itinerance}/tariff",
        params={"at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client_auth.put(
        f"/statique/{pdcs[1].id_pdc_itinerance}/tariff/{tariff_id}",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(tariff_id)
    assert set(response.json()["id_pdc_itinerance"]) == {
        pdcs[0].id_pdc_itinerance,
        pdcs[1].id_pdc_itinerance,
    }

    response = client_auth.get(
        f"/statique/{pdcs[1].id_pdc_itinerance}/tariff",
        params={"at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(tariff_id)

    response = client_auth.put(
        f"/statique/{pdcs[1].id_pdc_itinerance}/tariff/{tariff_id}",
    )
    assert response.status_code == status.HTTP_200_OK
    associations = db_session.exec(
        select(PointDeChargeTariff).where(PointDeChargeTariff.tariff_id == tariff_id)
    ).all()
    assert len(associations) == n_pdcs


def test_list_tariffs_pagination(db_session, client_auth):
    """Test the /statique/tariff/ list endpoint results pagination."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    total_tariffs = 3
    limit = 2
    second_page_offset = 2

    tariff_ids = []
    for index in range(total_tariffs):
        response = client_auth.post(
            "/statique/tariff/",
            json=_tariff_payload(
                f"tariff-{index}",
                now + timedelta(days=index),
                now + timedelta(days=index + 1),
                [pdc.id_pdc_itinerance],
            ),
        )
        assert response.status_code == status.HTTP_201_CREATED
        tariff_ids.append(response.json()["id"])

    response = client_auth.get(f"/statique/tariff/?offset=0&limit={limit}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["total"] == total_tariffs
    assert json_response["offset"] == 0
    assert json_response["limit"] == limit
    assert json_response["size"] == limit
    assert [tariff["id"] for tariff in json_response["items"]] == tariff_ids[:limit]
    assert json_response["previous"] is None
    next_query = parse_qs(urlparse(json_response["next"]).query)
    assert next_query == {"limit": ["2"], "offset": ["2"]}

    response = client_auth.get(
        f"/statique/tariff/?offset={second_page_offset}&limit={limit}"
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["total"] == total_tariffs
    assert json_response["offset"] == second_page_offset
    assert json_response["limit"] == limit
    assert json_response["size"] == 1
    assert [tariff["id"] for tariff in json_response["items"]] == tariff_ids[
        second_page_offset:
    ]
    previous_query = parse_qs(urlparse(json_response["previous"]).query)
    assert previous_query == {"limit": ["2"], "offset": ["0"]}
    assert json_response["next"] is None


def test_list_tariffs_filters_by_application_dates(db_session, client_auth):
    """Test tariff list filters by application dates."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    now = datetime.now(timezone.utc).replace(microsecond=0)

    expected = {
        "past": (
            now - timedelta(days=4),
            now - timedelta(days=3),
        ),
        "current": (
            now - timedelta(days=1),
            now + timedelta(days=1),
        ),
        "future": (
            now + timedelta(days=3),
            now + timedelta(days=4),
        ),
    }
    tariff_ids = {}
    for original_id, (start, end) in expected.items():
        response = client_auth.post(
            "/statique/tariff/",
            json=_tariff_payload(original_id, start, end, [pdc.id_pdc_itinerance]),
        )
        assert response.status_code == status.HTTP_201_CREATED
        tariff_ids[original_id] = response.json()["id"]

    response = client_auth.get("/statique/tariff/", params={"current": True})
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [
        tariff_ids["current"]
    ]

    response = client_auth.get(
        "/statique/tariff/",
        params={"from": (now + timedelta(days=2)).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [
        tariff_ids["future"]
    ]

    response = client_auth.get(
        "/statique/tariff/",
        params={"to": (now - timedelta(days=2)).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [tariff_ids["past"]]


def test_create_tariff_conflict(db_session, client_auth):
    """Test tariff creation conflict on original id and last update."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    payload = _tariff_payload("tariff-1", start, end, [pdc.id_pdc_itinerance])

    response = client_auth.post("/statique/tariff/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    response = client_auth.post("/statique/tariff/", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == (
        "Tariff with same original id and last update already exists"
    )


@pytest.mark.parametrize(
    "client_auth",
    (
        (
            True,
            {
                "is_superuser": False,
                "email": "jane@doe.com",
                "scopes": [ScopesEnum.TARIFF_CREATE],
            },
        ),
    ),
    indirect=True,
)
def test_create_tariff_for_user_with_forbidden_pdc(db_session, client_auth):
    """Test tariff creation cannot associate forbidden points of charge."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    response = client_auth.post(
        "/statique/tariff/",
        json=_tariff_payload("tariff-1", start, end, [pdc.id_pdc_itinerance]),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "client_auth",
    (
        (
            True,
            {
                "is_superuser": False,
                "email": "jane@doe.com",
                "scopes": [
                    ScopesEnum.TARIFF_CREATE,
                    ScopesEnum.TARIFF_READ,
                    ScopesEnum.TARIFF_UPDATE,
                ],
            },
        ),
    ),
    indirect=True,
)
def test_tariff_api_for_user_with_operational_unit(db_session, client_auth):
    """Test tariff workflow for a user scoped to a matching operational unit."""
    GroupFactory.__session__ = db_session
    save_statiques(
        db_session,
        [
            StatiqueFactory.build(
                id_pdc_itinerance="FRS63E0001",
                id_station_itinerance="FRS63P0001",
            ),
            StatiqueFactory.build(
                id_pdc_itinerance="FRS72E0001",
                id_station_itinerance="FRS72P0001",
            ),
        ],
    )
    user = db_session.exec(select(User).where(User.email == "jane@doe.com")).one()
    group = GroupFactory.create_sync()
    operational_unit = db_session.exec(
        select(OperationalUnit).where(OperationalUnit.code == "FRS63")
    ).one()
    db_session.add(
        GroupOperationalUnit(
            group_id=group.id,
            operational_unit_id=operational_unit.id,
        )
    )
    user.groups.append(group)

    pdcs = db_session.exec(select(PointDeCharge)).all()
    allowed_pdc = next(pdc for pdc in pdcs if pdc.id_pdc_itinerance == "FRS63E0001")
    forbidden_pdc = next(pdc for pdc in pdcs if pdc.id_pdc_itinerance == "FRS72E0001")
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    response = client_auth.post(
        "/statique/tariff/",
        json=_tariff_payload("tariff-1", start, end, [allowed_pdc.id_pdc_itinerance]),
    )
    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = response.json()["id"]

    response = client_auth.get("/statique/tariff/")
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [tariff_id]

    response = client_auth.get(
        "/statique/tariff/",
        params={"pdc": forbidden_pdc.id_pdc_itinerance},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["items"] == []

    response = client_auth.put(
        f"/statique/{forbidden_pdc.id_pdc_itinerance}/tariff/{tariff_id}",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
