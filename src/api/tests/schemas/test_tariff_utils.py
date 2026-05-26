"""Tests for tariff schema utilities."""

from datetime import datetime, timedelta, timezone

from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, UserFactory
from qualicharge.auth.schemas import GroupOperationalUnit
from qualicharge.factories.static import StatiqueFactory
from qualicharge.factories.tariff import (
    PointDeChargeTariffFactory,
    TariffFactory,
    TariffObjectFactory,
)
from qualicharge.schemas.core import OperationalUnit, PointDeCharge
from qualicharge.schemas.tariff import Tariff
from qualicharge.schemas.tariff_utils import (
    get_applicable_tariff_for_pdc,
    get_tariff_by_original,
    get_tariffs_pdc_ids,
    is_tariff_allowed_for_user,
)
from qualicharge.schemas.utils import save_statique


def _save_tariff(db_session, raw, created_by_id=None) -> Tariff:
    """Save a tariff from a raw tariff object."""
    TariffFactory.__session__ = db_session
    normalized_raw = raw.model_dump(by_alias=True, mode="json")
    return TariffFactory.create_sync(
        original_id=raw.tariff_id,
        original_last_updated=raw.last_updated,
        raw=normalized_raw,
        start=raw.tariff_application_date,
        end=raw.end_date_time,
        created_by_id=created_by_id,
        updated_by_id=created_by_id,
    )


def _associate(db_session, tariff: Tariff, pdc: PointDeCharge):
    """Associate a tariff and a point of charge."""
    PointDeChargeTariffFactory.__session__ = db_session
    return PointDeChargeTariffFactory.create_sync(
        tariff_id=tariff.id,
        point_de_charge_id=pdc.id,
        created_by_id=tariff.created_by_id,
        updated_by_id=tariff.updated_by_id,
    )


def test_tariff_database_datetimes_are_timezone_aware(db_session):
    """Test persisted tariff datetimes keep timezone information."""
    raw = TariffObjectFactory.build(
        id="tariff-1",
        last_updated=datetime(2026, 2, 23, 10, tzinfo=timezone.utc),
        start_date_time=datetime(2026, 2, 23, 11, tzinfo=timezone.utc),
        end_date_time=datetime(2026, 2, 23, 12, tzinfo=timezone.utc),
    )

    tariff = _save_tariff(db_session, raw)

    assert tariff.original_last_updated.tzinfo is not None
    assert tariff.start.tzinfo is not None
    assert tariff.end is not None
    assert tariff.end.tzinfo is not None


def test_tariff_to_read():
    """Test tariff to API read payload conversion."""
    raw = TariffObjectFactory.build(id="tariff-1")
    normalized_raw = raw.model_dump(by_alias=True, mode="json")
    tariff = Tariff(
        original_id=raw.tariff_id,
        original_last_updated=raw.last_updated,
        raw=normalized_raw,
        start=raw.tariff_application_date,
        end=raw.end_date_time,
    )
    ids_pdc_itinerance = ["FRS63E0001"]

    read = tariff.to_read(ids_pdc_itinerance)

    assert read.id == str(tariff.id)
    assert read.original_id == "FRQCHtariff-1"
    assert read.raw["id"] == "tariff-1"
    assert read.id_pdc_itinerance == ids_pdc_itinerance


def test_get_tariffs_pdc_ids(db_session):
    """Test charge point identifiers are grouped for several tariffs."""
    statiques = StatiqueFactory.batch(2)
    for index, statique in enumerate(statiques):
        statique.id_pdc_itinerance = f"FRS63E000{index}"
        statique.id_station_itinerance = f"FRS63P000{index}"
        save_statique(db_session, statique)
    pdcs = db_session.exec(select(PointDeCharge)).all()
    tariff_1 = _save_tariff(db_session, TariffObjectFactory.build(id="tariff-1"))
    tariff_2 = _save_tariff(db_session, TariffObjectFactory.build(id="tariff-2"))
    _associate(db_session, tariff_1, pdcs[0])
    _associate(db_session, tariff_1, pdcs[1])
    _associate(db_session, tariff_2, pdcs[1])

    pdc_ids_by_tariff_id = get_tariffs_pdc_ids(
        db_session,
        [tariff_1.id, tariff_2.id],
    )

    assert pdc_ids_by_tariff_id == {
        tariff_1.id: [pdcs[0].id_pdc_itinerance, pdcs[1].id_pdc_itinerance],
        tariff_2.id: [pdcs[1].id_pdc_itinerance],
    }


def test_get_tariff_by_original(db_session):
    """Test tariff lookup by original id and last update."""
    last_updated = datetime(2026, 2, 23, 10, tzinfo=timezone.utc)
    raw = TariffObjectFactory.build(
        id="tariff-1",
        last_updated=last_updated,
    )
    tariff = _save_tariff(db_session, raw)

    assert get_tariff_by_original(db_session, "FRQCHtariff-1", last_updated) == tariff

    tariff.deleted_at = datetime.now(timezone.utc)
    db_session.add(tariff)
    db_session.flush()
    assert get_tariff_by_original(db_session, "FRQCHtariff-1", last_updated) is None


def test_get_applicable_tariff_for_pdc(db_session):
    """Test applicable tariff lookup for a point of charge."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    save_statique(
        db_session,
        StatiqueFactory.build(
            id_pdc_itinerance="FRS63E0001",
            id_station_itinerance="FRS63P0001",
        ),
    )
    pdc = db_session.exec(select(PointDeCharge)).one()

    old = _save_tariff(
        db_session,
        TariffObjectFactory.build(
            id="old",
            start_date_time=now - timedelta(days=2),
            end_date_time=now + timedelta(days=2),
            last_updated=now - timedelta(hours=2),
        ),
    )
    selected = _save_tariff(
        db_session,
        TariffObjectFactory.build(
            id="selected",
            start_date_time=now - timedelta(hours=1),
            end_date_time=now + timedelta(days=2),
            last_updated=now - timedelta(hours=1),
        ),
    )
    future = _save_tariff(
        db_session,
        TariffObjectFactory.build(
            id="future",
            start_date_time=now + timedelta(hours=1),
            end_date_time=now + timedelta(days=2),
            last_updated=now,
        ),
    )
    deleted = _save_tariff(
        db_session,
        TariffObjectFactory.build(
            id="deleted",
            start_date_time=now,
            end_date_time=now + timedelta(days=2),
            last_updated=now,
        ),
    )
    deleted.deleted_at = now
    for tariff in (old, selected, future, deleted):
        _associate(db_session, tariff, pdc)

    pdc_exists, applicable_tariff = get_applicable_tariff_for_pdc(
        db_session,
        pdc.id_pdc_itinerance,
        now,
    )
    assert pdc_exists
    assert applicable_tariff == selected


def test_get_applicable_tariff_does_not_fallback_to_older_tariff(db_session):
    """Test an expired recent tariff supersedes older overlapping tariffs."""
    save_statique(
        db_session,
        StatiqueFactory.build(
            id_pdc_itinerance="FRS63E0001",
            id_station_itinerance="FRS63P0001",
        ),
    )
    pdc = db_session.exec(select(PointDeCharge)).one()
    date_a = datetime(2026, 1, 1, tzinfo=timezone.utc)
    date_b = datetime(2026, 1, 2, tzinfo=timezone.utc)
    date_c = datetime(2026, 1, 3, tzinfo=timezone.utc)
    date_d = datetime(2026, 1, 4, tzinfo=timezone.utc)
    date_e = datetime(2026, 1, 5, tzinfo=timezone.utc)

    old = _save_tariff(
        db_session,
        TariffObjectFactory.build(
            id="old",
            start_date_time=date_a,
            end_date_time=date_e,
            last_updated=date_a,
        ),
    )
    recent = _save_tariff(
        db_session,
        TariffObjectFactory.build(
            id="recent",
            start_date_time=date_b,
            end_date_time=date_c,
            last_updated=date_b,
        ),
    )
    _associate(db_session, old, pdc)
    _associate(db_session, recent, pdc)

    pdc_exists, applicable_tariff = get_applicable_tariff_for_pdc(
        db_session,
        pdc.id_pdc_itinerance,
        date_a + timedelta(hours=1),
    )
    assert pdc_exists
    assert applicable_tariff == old

    pdc_exists, applicable_tariff = get_applicable_tariff_for_pdc(
        db_session,
        pdc.id_pdc_itinerance,
        date_b + timedelta(hours=1),
    )
    assert pdc_exists
    assert applicable_tariff == recent

    pdc_exists, applicable_tariff = get_applicable_tariff_for_pdc(
        db_session,
        pdc.id_pdc_itinerance,
        date_d,
    )
    assert pdc_exists
    assert applicable_tariff is None


def test_get_applicable_tariff_uses_application_date(db_session):
    """Test tariff lookup does not apply a tariff before its last update."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    save_statique(
        db_session,
        StatiqueFactory.build(
            id_pdc_itinerance="FRS63E0001",
            id_station_itinerance="FRS63P0001",
        ),
    )
    pdc = db_session.exec(select(PointDeCharge)).one()
    tariff = _save_tariff(
        db_session,
        TariffObjectFactory.build(
            id="future-update",
            start_date_time=now - timedelta(days=1),
            last_updated=now + timedelta(hours=1),
            end_date_time=now + timedelta(days=1),
        ),
    )
    _associate(db_session, tariff, pdc)

    pdc_exists, applicable_tariff = get_applicable_tariff_for_pdc(
        db_session,
        pdc.id_pdc_itinerance,
        now,
    )
    assert pdc_exists
    assert applicable_tariff is None

    pdc_exists, applicable_tariff = get_applicable_tariff_for_pdc(
        db_session,
        pdc.id_pdc_itinerance,
        now + timedelta(hours=1),
    )
    assert pdc_exists
    assert applicable_tariff == tariff


def test_get_applicable_tariff_for_pdc_with_unknown_pdc(db_session):
    """Test applicable tariff lookup preserves unknown charge point detection."""
    pdc_exists, applicable_tariff = get_applicable_tariff_for_pdc(
        db_session,
        "FRS63E404",
        datetime.now(timezone.utc),
    )

    assert not pdc_exists
    assert applicable_tariff is None


def test_is_tariff_allowed_for_user(db_session):
    """Test tariff access checks."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    save_statique(
        db_session,
        StatiqueFactory.build(
            id_pdc_itinerance="FRS63E0001",
            id_station_itinerance="FRS63P0001",
        ),
    )
    pdc = db_session.exec(select(PointDeCharge)).one()
    tariff = _save_tariff(db_session, TariffObjectFactory.build(id="tariff-1"))
    _associate(db_session, tariff, pdc)

    superuser = UserFactory.create_sync(is_superuser=True)
    assert is_tariff_allowed_for_user(
        tariff,
        [pdc.id_pdc_itinerance],
        superuser,
    )

    owner = UserFactory.create_sync(is_superuser=False)
    owned_tariff = _save_tariff(
        db_session,
        TariffObjectFactory.build(id="owned"),
        created_by_id=owner.id,
    )
    assert is_tariff_allowed_for_user(owned_tariff, [], owner)

    unrelated = UserFactory.create_sync(is_superuser=False)
    assert not is_tariff_allowed_for_user(
        tariff,
        [pdc.id_pdc_itinerance],
        unrelated,
    )

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
    allowed = UserFactory.create_sync(is_superuser=False, groups=[group])
    assert is_tariff_allowed_for_user(
        tariff,
        [pdc.id_pdc_itinerance],
        allowed,
    )
