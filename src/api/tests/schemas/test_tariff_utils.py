"""Tests for tariff schema utilities."""

from datetime import datetime, timedelta, timezone

from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, UserFactory
from qualicharge.auth.schemas import GroupOperationalUnit
from qualicharge.factories.static import StatiqueFactory
from qualicharge.factories.tariff import TariffObjectFactory
from qualicharge.schemas.core import OperationalUnit, PointDeCharge
from qualicharge.schemas.tariff import PointDeChargeTariff, Tariff
from qualicharge.schemas.tariff_utils import (
    get_applicable_tariff,
    get_tariff_by_original,
    is_tariff_allowed_for_user,
    tariff_fields_from_object,
    tariff_to_read,
    to_db_datetime,
)
from qualicharge.schemas.utils import save_statique, save_statiques


def _save_tariff(db_session, raw, created_by_id=None) -> Tariff:
    """Save a tariff from a raw tariff object."""
    tariff = Tariff(
        **tariff_fields_from_object(raw),
        created_by_id=created_by_id,
        updated_by_id=created_by_id,
    )
    db_session.add(tariff)
    db_session.flush()
    return tariff


def _associate(db_session, tariff: Tariff, pdc: PointDeCharge):
    """Associate a tariff and a point of charge."""
    association = PointDeChargeTariff(
        tariff_id=tariff.id,
        point_de_charge_id=pdc.id,
        created_by_id=tariff.created_by_id,
        updated_by_id=tariff.updated_by_id,
    )
    db_session.add(association)
    db_session.flush()
    return association


def test_to_db_datetime():
    """Test aware datetime conversion to naive UTC datetimes."""
    value = datetime(2026, 2, 23, 10, 30, tzinfo=timezone(timedelta(hours=1)))

    assert to_db_datetime(None) is None
    assert to_db_datetime(datetime(2026, 2, 23, 9, 30)) == datetime(
        2026,
        2,
        23,
        9,
        30,
    )
    assert to_db_datetime(value) == datetime(2026, 2, 23, 9, 30)


def test_tariff_fields_from_object():
    """Test extraction of tariff database fields from a tariff object."""
    start = datetime(2026, 2, 23, 10, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)
    last_updated = start - timedelta(hours=1)
    raw = TariffObjectFactory.build(
        id="tariff-1",
        last_updated=last_updated,
        start_date_time=start,
        end_date_time=end,
    )

    fields = tariff_fields_from_object(raw)

    assert fields["original_id"] == "FRQCHtariff-1"
    assert fields["original_last_updated"] == datetime(2026, 2, 23, 9)
    assert fields["start"] == datetime(2026, 2, 23, 10)
    assert fields["end"] == datetime(2026, 2, 23, 12)
    assert fields["raw"]["id"] == "tariff-1"
    assert "tariff_id" not in fields["raw"]


def test_tariff_fields_from_object_uses_application_date_for_start():
    """Test tariff database start uses the computed application date."""
    last_updated = datetime(2026, 2, 23, 10, tzinfo=timezone.utc)
    raw = TariffObjectFactory.build(
        id="tariff-1",
        last_updated=last_updated,
        start_date_time=last_updated - timedelta(hours=1),
        end_date_time=last_updated + timedelta(hours=1),
    )

    fields = tariff_fields_from_object(raw)

    assert fields["start"] == datetime(2026, 2, 23, 10)


def test_tariff_to_read(db_session):
    """Test tariff SQL to read payload conversion."""
    statiques = StatiqueFactory.batch(2)
    save_statiques(db_session, statiques)
    pdcs = db_session.exec(select(PointDeCharge)).all()
    raw = TariffObjectFactory.build(id="tariff-1")
    tariff = _save_tariff(db_session, raw)
    _associate(db_session, tariff, pdcs[0])

    read = tariff_to_read(db_session, tariff)

    assert read.id == str(tariff.id)
    assert read.original_id == "FRQCHtariff-1"
    assert read.raw.id == "tariff-1"
    assert read.raw.tariff_id == "FRQCHtariff-1"
    assert read.id_pdc_itinerance == [pdcs[0].id_pdc_itinerance]


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


def test_get_applicable_tariff(db_session):
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
    db_session.add(deleted)
    for tariff in (old, selected, future, deleted):
        _associate(db_session, tariff, pdc)

    assert get_applicable_tariff(db_session, pdc.id, to_db_datetime(now)) == selected


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

    assert get_applicable_tariff(db_session, pdc.id, to_db_datetime(now)) is None
    assert (
        get_applicable_tariff(
            db_session,
            pdc.id,
            to_db_datetime(now + timedelta(hours=1)),
        )
        == tariff
    )


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
    assert is_tariff_allowed_for_user(db_session, tariff.id, superuser) is True

    owner = UserFactory.create_sync(is_superuser=False)
    owned_tariff = _save_tariff(
        db_session,
        TariffObjectFactory.build(id="owned"),
        created_by_id=owner.id,
    )
    assert is_tariff_allowed_for_user(db_session, owned_tariff.id, owner) is True

    unrelated = UserFactory.create_sync(is_superuser=False)
    assert is_tariff_allowed_for_user(db_session, tariff.id, unrelated) is False

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
    assert is_tariff_allowed_for_user(db_session, tariff.id, allowed) is True
