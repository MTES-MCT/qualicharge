"""Tariff persistence and mapping helpers."""

from datetime import datetime, timezone
from typing import Optional, cast
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, select

from qualicharge.auth.schemas import User
from qualicharge.models.tariff import TariffObject, TariffRead
from qualicharge.schemas.core import (
    ActivePointsDeChargeView,
    ActiveStationsView,
    PointDeCharge,
)
from qualicharge.schemas.tariff import PointDeChargeTariff, Tariff


def to_db_datetime(value: Optional[datetime]) -> Optional[datetime]:
    """Convert an aware datetime to naive UTC for tariff SQL columns."""
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def tariff_fields_from_object(raw: TariffObject) -> dict:
    """Extract indexed database fields from a tariff object."""
    return {
        "original_id": raw.tariff_id,
        "original_last_updated": to_db_datetime(raw.last_updated),
        "raw": raw.model_dump(by_alias=True, mode="json"),
        "start": to_db_datetime(raw.start_date_time),
        "end": to_db_datetime(raw.end_date_time),
    }


def tariff_to_read(session: Session, tariff: Tariff) -> TariffRead:
    """Convert a database tariff to API output."""
    pdc_ids = session.exec(
        select(PointDeCharge.id_pdc_itinerance)
        .join(
            PointDeChargeTariff,
            cast(SAColumn, PointDeCharge.id)
            == cast(SAColumn, PointDeChargeTariff.point_de_charge_id),
        )
        .where(cast(SAColumn, PointDeChargeTariff.tariff_id) == tariff.id)
    ).all()
    return TariffRead(
        id=str(tariff.id),
        original_id=tariff.original_id,
        original_last_updated=tariff.original_last_updated,
        raw=TariffObject.model_validate(tariff.raw),
        start=tariff.start,
        end=tariff.end,
        id_pdc_itinerance=list(pdc_ids),
    )


def get_tariff_by_original(
    session: Session,
    original_id: str,
    original_last_updated: Optional[datetime],
) -> Optional[Tariff]:
    """Get an active tariff from its operator identifier."""
    original_last_updated = to_db_datetime(original_last_updated)
    stmt = select(Tariff).where(
        Tariff.original_id == original_id,
        cast(SAColumn, Tariff.deleted_at).is_(None),
    )
    if original_last_updated is None:
        stmt = stmt.where(cast(SAColumn, Tariff.original_last_updated).is_(None))
    else:
        stmt = stmt.where(
            cast(SAColumn, Tariff.original_last_updated) == original_last_updated
        )
    return session.exec(stmt).one_or_none()


def is_tariff_allowed_for_user(
    session: Session,
    tariff_id: UUID,
    user: User,
) -> bool:
    """Return whether a user can access a tariff."""
    if user.is_superuser:
        return True

    if (
        session.exec(
            select(Tariff.created_by_id).where(
                Tariff.id == tariff_id,
                Tariff.created_by_id == user.id,
            )
        ).one_or_none()
        is not None
    ):
        return True

    stmt = (
        select(PointDeChargeTariff.tariff_id)
        .join(
            ActivePointsDeChargeView,
            cast(SAColumn, PointDeChargeTariff.point_de_charge_id)
            == cast(SAColumn, ActivePointsDeChargeView.id),  # type: ignore[attr-defined]
        )
        .join(
            ActiveStationsView,
            cast(SAColumn, ActivePointsDeChargeView.station_id)  # type: ignore[attr-defined]
            == cast(SAColumn, ActiveStationsView.id),  # type: ignore[attr-defined]
        )
        .where(PointDeChargeTariff.tariff_id == tariff_id)
        .where(
            cast(SAColumn, ActiveStationsView.operational_unit_id).in_(  # type: ignore[attr-defined]
                [ou.id for ou in user.operational_units]
            )
        )
    )
    return session.exec(stmt).first() is not None


def get_applicable_tariff(
    session: Session,
    point_de_charge_id,
    at: datetime,
) -> Optional[Tariff]:
    """Get applicable tariff for a charge point at a given datetime."""
    stmt = (
        select(Tariff)
        .join(
            PointDeChargeTariff,
            cast(SAColumn, PointDeChargeTariff.tariff_id) == cast(SAColumn, Tariff.id),
        )
        .where(PointDeChargeTariff.point_de_charge_id == point_de_charge_id)
        .where(cast(SAColumn, Tariff.deleted_at).is_(None))
        .where(
            cast(SAColumn, Tariff.start).is_(None)
            | (cast(SAColumn, Tariff.start) <= at)
        )
        .where(cast(SAColumn, Tariff.end).is_(None) | (cast(SAColumn, Tariff.end) > at))
        .order_by(
            desc(cast(SAColumn, Tariff.start).is_not(None)),
            desc(cast(SAColumn, Tariff.start)),
            desc(cast(SAColumn, Tariff.original_last_updated)),
            desc(cast(SAColumn, Tariff.created_at)),
        )
    )
    return session.exec(stmt).first()
