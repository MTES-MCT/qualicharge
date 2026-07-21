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
from qualicharge.models.fields import IdPdcItinerance
from qualicharge.schemas.core import OperationalUnit, PointDeCharge
from qualicharge.schemas.tariff import PointDeChargeTariff, Tariff
from qualicharge.schemas.utils import save_statiques


def _tariff_payload(
    id_: str, start: datetime, end: datetime | None, pdcs: list[IdPdcItinerance]
) -> dict:
    """Build a tariff creation payload."""
    raw = TariffObjectFactory.build(
        id=id_,
        last_updated=start,
        start_date_time=start,
        end_date_time=end,
    )
    return TariffCreateFactory.build(
        tariff=raw,
        targets=pdcs,
    ).model_dump(by_alias=True, mode="json")


def _save_tariff(
    db_session,
    id_: str,
    start: datetime,
    end: datetime | None,
    pdcs: list[PointDeCharge] | None = None,
) -> Tariff:
    """Save a tariff and optional charge point associations."""
    raw = TariffObjectFactory.build(
        id=id_,
        last_updated=start,
        start_date_time=start,
        end_date_time=end,
    )
    tariff = Tariff(
        original_id=raw.tariff_id,
        original_last_updated=raw.last_updated,
        raw=raw.model_dump(by_alias=True, mode="json"),
        start=raw.tariff_application_date,
        end=raw.end_date_time,
    )
    db_session.add(tariff)
    db_session.flush()

    for pdc in pdcs or []:
        db_session.add(
            PointDeChargeTariff(
                point_de_charge_id=pdc.id,
                tariff_id=tariff.id,
            )
        )
    db_session.flush()
    return tariff


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

    assert client_auth.get("/tariff/").status_code == status.HTTP_403_FORBIDDEN
    assert (
        client_auth.post("/tariff/", json={}).status_code == status.HTTP_403_FORBIDDEN
    )
    assert (
        client_auth.get(f"/tariff/{tariff_id}").status_code == status.HTTP_403_FORBIDDEN
    )
    assert (
        client_auth.put(
            "/tariff/chargepoint/FRS63E0001",
            json={"tariff_id": str(tariff_id)},
        ).status_code
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

    response = client_auth.post("/tariff/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    created = response.json()
    tariff_id = UUID(created["id"])
    assert created["original_id"] == "FRQCHtariff-1"
    assert created["id_pdc_itinerance"] == [pdcs[0].id_pdc_itinerance]

    db_tariff = db_session.get(Tariff, tariff_id)
    assert db_tariff is not None
    assert db_tariff.deleted_at is None

    response = client_auth.get("/tariff/")
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [str(tariff_id)]

    response = client_auth.get(f"/tariff/{tariff_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(tariff_id)

    response = client_auth.get(
        f"/tariff/{pdcs[0].id_pdc_itinerance}/applicable",
        params={"at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(tariff_id)

    response = client_auth.get(
        f"/tariff/{pdcs[1].id_pdc_itinerance}/applicable",
        params={"at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client_auth.put(
        f"/tariff/chargepoint/{pdcs[1].id_pdc_itinerance}",
        json={"tariff_id": str(tariff_id)},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(tariff_id)
    assert set(response.json()["id_pdc_itinerance"]) == {
        pdcs[0].id_pdc_itinerance,
        pdcs[1].id_pdc_itinerance,
    }

    response = client_auth.get(
        f"/tariff/{pdcs[1].id_pdc_itinerance}/applicable",
        params={"at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(tariff_id)

    response = client_auth.put(
        f"/tariff/chargepoint/{pdcs[1].id_pdc_itinerance}",
        json={"tariff_id": str(tariff_id)},
    )
    assert response.status_code == status.HTTP_200_OK
    associations = db_session.exec(
        select(PointDeChargeTariff).where(PointDeChargeTariff.tariff_id == tariff_id)
    ).all()
    assert len(associations) == n_pdcs


@pytest.mark.parametrize(
    ("target_data", "error_type", "error_message"),
    (
        pytest.param({}, "missing", "Field required", id="missing"),
        pytest.param(
            {"targets": []},
            "too_short",
            "List should have at least 1 item after validation, not 0",
            id="empty",
        ),
        pytest.param(
            {"targets": None},
            "list_type",
            "Input should be a valid list",
            id="null",
        ),
    ),
)
def test_create_tariff_rejects_missing_empty_or_null_targets(
    db_session,
    client_auth,
    target_data,
    error_type,
    error_message,
):
    """Test tariff creation rejects payloads without associated charge points."""
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    payload = _tariff_payload("tariff-1", start, end, ["FRS63E0001"])
    del payload["targets"]
    payload.update(target_data)

    response = client_auth.post(
        "/tariff/",
        json=payload,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["loc"] == ["body", "targets"]
    assert errors[0]["type"] == error_type
    assert errors[0]["msg"] == error_message
    assert db_session.exec(select(Tariff)).all() == []


def test_create_tariff_stores_extra_raw_fields(db_session, client_auth):
    """Test tariff creation stores validated payload with extra fields."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    payload = _tariff_payload("tariff-1", start, end, [pdc.id_pdc_itinerance])
    payload["tariff"]["custom_tariff"] = {"source": "operator"}
    payload["tariff"]["elements"][0]["custom_element"] = "element-extra"
    payload["tariff"]["elements"][0]["price_components"][0]["billing_unit"] = "kWh"

    response = client_auth.post("/tariff/", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = UUID(response.json()["id"])
    db_tariff = db_session.get(Tariff, tariff_id)
    assert db_tariff is not None
    assert db_tariff.raw == payload["tariff"]
    assert db_tariff.raw["custom_tariff"] == {"source": "operator"}
    assert db_tariff.raw["elements"][0]["custom_element"] == "element-extra"
    assert db_tariff.raw["elements"][0]["price_components"][0]["billing_unit"] == (
        "kWh"
    )
    assert response.json()["raw"] == db_tariff.raw


def test_create_tariff_stores_submitted_raw_payload(db_session, client_auth):
    """Test tariff creation stores the submitted tariff payload as raw data."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    payload = {
        "targets": [pdc.id_pdc_itinerance],
        "tariff": {
            "country_code": "FR",
            "party_id": "QCH",
            "id": "tariff-1",
            "last_updated": "2026-01-01T12:00:00Z",
            "elements": [
                {
                    "price_components": [
                        {
                            "type": "ENERGY",
                            "price": 0.3,
                        }
                    ],
                    "restrictions": {
                        "start_time": "06:00",
                        "end_time": "18:30",
                        "start_date": "2026-01-01",
                        "end_date": "2026-12-31",
                    },
                }
            ],
            "custom_tariff": {"source": "operator"},
        },
    }

    response = client_auth.post("/tariff/", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = UUID(response.json()["id"])
    db_tariff = db_session.get(Tariff, tariff_id)
    assert db_tariff is not None
    assert db_tariff.raw == payload["tariff"]
    assert response.json()["raw"] == payload["tariff"]
    assert "currency" not in db_tariff.raw
    assert "tax_included" not in db_tariff.raw
    assert "start_date_time" not in db_tariff.raw
    assert "end_date_time" not in db_tariff.raw
    assert db_tariff.raw["elements"][0]["restrictions"]["start_time"] == "06:00"
    assert db_tariff.raw["elements"][0]["restrictions"]["end_time"] == "18:30"


def test_create_tariff_rejects_invalid_known_field(client_auth):
    """Test tariff creation still validates known tariff fields."""
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    payload = _tariff_payload("tariff-1", start, end, ["FRS63E0001"])
    payload["tariff"]["currency"] = "USD"

    response = client_auth.post("/tariff/", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["loc"] == ["body", "tariff", "currency"]
    assert errors[0]["type"] == "literal_error"
    assert errors[0]["msg"] == "Input should be 'EUR'"


def test_create_tariff_with_unknown_pdc_rolls_back(db_session, client_auth):
    """Test tariff creation fails and rolls back when a target is unknown."""
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload("tariff-1", start, end, ["FRS63E404"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Point of charge does not exist"
    assert (
        db_session.exec(
            select(Tariff).where(Tariff.original_id == "FRQCHtariff-1")
        ).one_or_none()
        is None
    )


def test_create_tariff_with_duplicate_targets(db_session, client_auth):
    """Test duplicate targets create a single association."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload(
            "tariff-1",
            start,
            end,
            [pdc.id_pdc_itinerance, pdc.id_pdc_itinerance],
        ),
    )

    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = UUID(response.json()["id"])
    assert response.json()["id_pdc_itinerance"] == [pdc.id_pdc_itinerance]
    assert (
        len(
            db_session.exec(
                select(PointDeChargeTariff).where(
                    PointDeChargeTariff.tariff_id == tariff_id
                )
            ).all()
        )
        == 1
    )


def test_list_tariffs_pagination(db_session, client_auth):
    """Test the /tariff/ list endpoint results pagination."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    total_tariffs = 3
    limit = 2
    second_page_offset = 2

    tariff_ids = []
    for index in range(total_tariffs):
        response = client_auth.post(
            "/tariff/",
            json=_tariff_payload(
                f"tariff-{index}",
                now + timedelta(days=index),
                now + timedelta(days=index + 1),
                [pdc.id_pdc_itinerance],
            ),
        )
        assert response.status_code == status.HTTP_201_CREATED
        tariff_ids.append(response.json()["id"])

    response = client_auth.get(f"/tariff/?offset=0&limit={limit}")
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

    response = client_auth.get(f"/tariff/?offset={second_page_offset}&limit={limit}")
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


def test_list_tariffs_filters_by_multiple_pdcs_without_duplicates(
    db_session,
    client_auth,
):
    """Test PDC filtering keeps one tariff row when several targets match."""
    n_pdcs = 2
    save_statiques(db_session, StatiqueFactory.batch(n_pdcs))
    pdcs = db_session.exec(select(PointDeCharge)).all()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload(
            "tariff-1",
            start,
            end,
            [pdc.id_pdc_itinerance for pdc in pdcs],
        ),
    )
    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = response.json()["id"]

    response = client_auth.get(
        "/tariff/",
        params=[("pdc", pdc.id_pdc_itinerance) for pdc in pdcs],
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 1
    assert [tariff["id"] for tariff in response.json()["items"]] == [tariff_id]


@pytest.mark.parametrize(
    "params",
    [
        {"offset": -1},
        {"limit": 1001},
    ],
)
def test_list_tariffs_rejects_invalid_pagination(client_auth, params):
    """Test tariff list pagination bounds."""
    response = client_auth.get("/tariff/", params=params)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_tariff_with_multiple_targets(db_session, client_auth):
    """Test tariff creation resolves several charge points at once."""
    n_pdcs = 2
    save_statiques(db_session, StatiqueFactory.batch(n_pdcs))
    pdcs = db_session.exec(select(PointDeCharge)).all()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload(
            "tariff-1",
            start,
            end,
            [pdc.id_pdc_itinerance for pdc in pdcs],
        ),
    )

    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = UUID(response.json()["id"])
    assert set(response.json()["id_pdc_itinerance"]) == {
        pdc.id_pdc_itinerance for pdc in pdcs
    }
    associations = db_session.exec(
        select(PointDeChargeTariff).where(PointDeChargeTariff.tariff_id == tariff_id)
    ).all()
    assert len(associations) == n_pdcs


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
            "/tariff/",
            json=_tariff_payload(original_id, start, end, [pdc.id_pdc_itinerance]),
        )
        assert response.status_code == status.HTTP_201_CREATED
        tariff_ids[original_id] = response.json()["id"]

    response = client_auth.get("/tariff/", params={"current": True})
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [
        tariff_ids["current"]
    ]

    response = client_auth.get(
        "/tariff/",
        params={"from": (now + timedelta(days=2)).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [
        tariff_ids["future"]
    ]

    response = client_auth.get(
        "/tariff/",
        params={"to": (now - timedelta(days=2)).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [tariff_ids["past"]]

    response = client_auth.get(
        "/tariff/",
        params={"original_id": "FRQCHcurrent"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [
        tariff_ids["current"]
    ]

    response = client_auth.get(
        "/tariff/",
        params={"original_id": "FRQCHunknown"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["items"] == []


def test_open_ended_tariff_is_current_and_applicable(db_session, client_auth):
    """Test tariffs without end date stay current and applicable."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=1)

    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload("tariff-1", start, None, [pdc.id_pdc_itinerance]),
    )
    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = response.json()["id"]
    assert response.json()["end"] is None

    response = client_auth.get("/tariff/", params={"current": True})
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [tariff_id]

    response = client_auth.get(
        f"/tariff/{pdc.id_pdc_itinerance}/applicable",
        params={"at": (start + timedelta(days=30)).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == tariff_id


def test_list_tariffs_rejects_naive_application_dates(client_auth):
    """Test tariff list date filters require timezone-aware datetimes."""
    response = client_auth.get(
        "/tariff/",
        params={"from": datetime(2026, 1, 1, 12).isoformat()},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_applicable_tariff_does_not_fallback_to_older_tariff(db_session, client_auth):
    """Test an expired recent tariff supersedes older overlapping tariffs."""
    save_statiques(
        db_session,
        [
            StatiqueFactory.build(
                id_pdc_itinerance="FRS63E0001",
                id_station_itinerance="FRS63P0001",
            )
        ],
    )
    pdc = db_session.exec(select(PointDeCharge)).one()

    date_a = datetime(2026, 1, 1, tzinfo=timezone.utc)
    date_b = datetime(2026, 1, 2, tzinfo=timezone.utc)
    date_c = datetime(2026, 1, 3, tzinfo=timezone.utc)
    date_d = datetime(2026, 1, 4, tzinfo=timezone.utc)
    date_e = datetime(2026, 1, 5, tzinfo=timezone.utc)

    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload("tariff-1", date_a, date_e, [pdc.id_pdc_itinerance]),
    )
    assert response.status_code == status.HTTP_201_CREATED
    tariff_1_id = response.json()["id"]

    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload("tariff-2", date_b, date_c, [pdc.id_pdc_itinerance]),
    )
    assert response.status_code == status.HTTP_201_CREATED
    tariff_2_id = response.json()["id"]

    response = client_auth.get(
        f"/tariff/{pdc.id_pdc_itinerance}/applicable",
        params={"at": (date_a + timedelta(hours=1)).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == tariff_1_id

    response = client_auth.get(
        f"/tariff/{pdc.id_pdc_itinerance}/applicable",
        params={"at": (date_b + timedelta(hours=1)).isoformat()},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == tariff_2_id

    response = client_auth.get(
        f"/tariff/{pdc.id_pdc_itinerance}/applicable",
        params={"at": date_d.isoformat()},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_applicable_tariff_rejects_naive_application_date(client_auth):
    """Test applicable tariff lookup requires a timezone-aware datetime."""
    response = client_auth.get(
        "/tariff/FRS63E0001/applicable",
        params={"at": datetime(2026, 1, 1, 12).isoformat()},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_read_applicable_tariff_uses_current_time_by_default(db_session, client_auth):
    """Test applicable tariff lookup defaults to the current time."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=1)
    end = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=1)

    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload("tariff-1", start, end, [pdc.id_pdc_itinerance]),
    )
    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = response.json()["id"]

    response = client_auth.get(f"/tariff/{pdc.id_pdc_itinerance}/applicable")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == tariff_id


def test_read_missing_tariff(client_auth):
    """Test reading an unknown tariff returns a 404."""
    response = client_auth.get(f"/tariff/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Tariff does not exist"


@pytest.mark.parametrize(
    "client_auth",
    (
        (
            True,
            {
                "is_superuser": False,
                "email": "jane@doe.com",
                "scopes": [ScopesEnum.TARIFF_READ],
            },
        ),
    ),
    indirect=True,
)
def test_read_tariff_forbidden_for_user(db_session, client_auth):
    """Test users cannot read tariffs outside their operational units."""
    save_statiques(
        db_session,
        [
            StatiqueFactory.build(
                id_pdc_itinerance="FRS63E0001",
                id_station_itinerance="FRS63P0001",
            )
        ],
    )
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    tariff = _save_tariff(db_session, "tariff-1", start, end, [pdc])

    response = client_auth.get(f"/tariff/{tariff.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["message"] == (
        "Unsufficient permissions: You cannot access this tariff"
    )


def test_read_applicable_tariff_for_unknown_pdc(client_auth):
    """Test applicable tariff lookup keeps unknown PDC errors explicit."""
    response = client_auth.get(
        "/tariff/FRS63E404/applicable",
        params={"at": datetime.now(timezone.utc).isoformat()},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Point of charge does not exist"


@pytest.mark.parametrize(
    "client_auth",
    (
        (
            True,
            {
                "is_superuser": False,
                "email": "jane@doe.com",
                "scopes": [ScopesEnum.TARIFF_READ],
            },
        ),
    ),
    indirect=True,
)
def test_read_applicable_tariff_forbidden_for_user(db_session, client_auth):
    """Test users cannot read applicable tariff for forbidden charge points."""
    save_statiques(
        db_session,
        [
            StatiqueFactory.build(
                id_pdc_itinerance="FRS63E0001",
                id_station_itinerance="FRS63P0001",
            )
        ],
    )
    pdc = db_session.exec(select(PointDeCharge)).one()

    response = client_auth.get(
        f"/tariff/{pdc.id_pdc_itinerance}/applicable",
        params={"at": datetime.now(timezone.utc).isoformat()},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["message"] == (
        "Unsufficient permissions: You cannot read tariff for this point of charge"
    )


def test_apply_tariff_with_unknown_tariff(db_session, client_auth):
    """Test applying an unknown tariff returns a 404."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()

    response = client_auth.put(
        f"/tariff/chargepoint/{pdc.id_pdc_itinerance}",
        json={"tariff_id": str(uuid4())},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Tariff does not exist"


@pytest.mark.parametrize(
    "client_auth",
    (
        (
            True,
            {
                "is_superuser": False,
                "email": "jane@doe.com",
                "scopes": [ScopesEnum.TARIFF_UPDATE],
            },
        ),
    ),
    indirect=True,
)
def test_apply_tariff_with_forbidden_tariff_for_user(db_session, client_auth):
    """Test users cannot apply tariffs they cannot access."""
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
    tariff = _save_tariff(db_session, "tariff-1", start, end, [forbidden_pdc])

    response = client_auth.put(
        f"/tariff/chargepoint/{allowed_pdc.id_pdc_itinerance}",
        json={"tariff_id": str(tariff.id)},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["message"] == (
        "Unsufficient permissions: You cannot access this tariff"
    )
    associations = db_session.exec(
        select(PointDeChargeTariff).where(PointDeChargeTariff.tariff_id == tariff.id)
    ).all()
    assert {association.point_de_charge_id for association in associations} == {
        forbidden_pdc.id
    }


def test_apply_tariff_with_unknown_pdc_rolls_back(db_session, client_auth):
    """Test applying a tariff to an unknown PDC returns a 404."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload("tariff-1", start, end, [pdc.id_pdc_itinerance]),
    )
    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = UUID(response.json()["id"])

    response = client_auth.put(
        "/tariff/chargepoint/FRS63E404",
        json={"tariff_id": str(tariff_id)},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Point of charge does not exist"
    associations = db_session.exec(
        select(PointDeChargeTariff).where(PointDeChargeTariff.tariff_id == tariff_id)
    ).all()
    assert len(associations) == 1
    assert associations[0].point_de_charge_id == pdc.id


def test_deleted_tariff_is_hidden(db_session, client_auth):
    """Test soft-deleted tariffs cannot be listed, read or applied."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    response = client_auth.post(
        "/tariff/",
        json=_tariff_payload("tariff-1", start, end, [pdc.id_pdc_itinerance]),
    )
    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = UUID(response.json()["id"])
    tariff = db_session.get(Tariff, tariff_id)
    assert tariff is not None
    tariff.deleted_at = datetime.now(timezone.utc)
    db_session.add(tariff)
    db_session.commit()

    response = client_auth.get("/tariff/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["items"] == []

    response = client_auth.get(f"/tariff/{tariff_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client_auth.get(
        f"/tariff/{pdc.id_pdc_itinerance}/applicable",
        params={"at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client_auth.put(
        f"/tariff/chargepoint/{pdc.id_pdc_itinerance}",
        json={"tariff_id": str(tariff_id)},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_tariff_conflict(db_session, client_auth):
    """Test tariff creation conflict on original id and last update."""
    save_statiques(db_session, StatiqueFactory.batch(1))
    pdc = db_session.exec(select(PointDeCharge)).one()
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    payload = _tariff_payload("tariff-1", start, end, [pdc.id_pdc_itinerance])

    response = client_auth.post("/tariff/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    response = client_auth.post("/tariff/", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Tariff already exists or cannot be associated"


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
        "/tariff/",
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
        "/tariff/",
        json=_tariff_payload("tariff-1", start, end, [allowed_pdc.id_pdc_itinerance]),
    )
    assert response.status_code == status.HTTP_201_CREATED
    tariff_id = response.json()["id"]

    response = client_auth.get("/tariff/")
    assert response.status_code == status.HTTP_200_OK
    assert [tariff["id"] for tariff in response.json()["items"]] == [tariff_id]

    response = client_auth.get(
        "/tariff/",
        params={"pdc": forbidden_pdc.id_pdc_itinerance},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["items"] == []

    response = client_auth.put(
        f"/tariff/chargepoint/{forbidden_pdc.id_pdc_itinerance}",
        json={"tariff_id": tariff_id},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
