"""Tariff persistence and mapping helpers."""

from collections import defaultdict
from datetime import datetime
from typing import Optional, Sequence, cast
from uuid import UUID

from sqlalchemy import and_, desc, nullslast
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, select

from qualicharge.auth.schemas import User
from qualicharge.models.fields import IdPdcItinerance
from qualicharge.schemas.core import ActivePointsDeChargeView, PointDeCharge
from qualicharge.schemas.tariff import PointDeChargeTariff, Tariff
from qualicharge.schemas.utils import is_pdc_allowed_for_user


def get_tariffs_pdc_ids(
    session: Session,
    tariff_ids: Sequence[UUID],
) -> dict[UUID, list[IdPdcItinerance]]:
    """Return API charge point identifiers grouped by tariff id."""
    if not tariff_ids:
        return {}

    stmt = (
        select(PointDeChargeTariff.tariff_id, PointDeCharge.id_pdc_itinerance)
        .join(
            PointDeCharge,
            cast(SAColumn, PointDeCharge.id)
            == cast(SAColumn, PointDeChargeTariff.point_de_charge_id),
        )
        .where(cast(SAColumn, PointDeChargeTariff.tariff_id).in_(tariff_ids))
    )
    pdc_ids_by_tariff_id: dict[UUID, list[IdPdcItinerance]] = defaultdict(list)
    for tariff_id, id_pdc_itinerance in session.exec(stmt).all():
        pdc_ids_by_tariff_id[tariff_id].append(id_pdc_itinerance)
    return dict(pdc_ids_by_tariff_id)


def get_tariff_pdc_ids(
    session: Session,
    tariff: Tariff,
) -> list[IdPdcItinerance]:
    """Return API charge point identifiers associated with a tariff."""
    return get_tariffs_pdc_ids(session, [tariff.id]).get(tariff.id, [])


def get_tariff_by_original(
    session: Session,
    original_id: str,
    original_last_updated: datetime,
) -> Optional[Tariff]:
    """Get an active tariff from its operator identifier."""
    stmt = select(Tariff).where(
        Tariff.original_id == original_id,
        cast(SAColumn, Tariff.deleted_at).is_(None),
        cast(SAColumn, Tariff.original_last_updated) == original_last_updated,
    )
    return session.exec(stmt).one_or_none()


def is_tariff_allowed_for_user(
    tariff: Tariff,
    ids_pdc_itinerance: Sequence[IdPdcItinerance],
    user: User,
) -> bool:
    """Return whether a user can access a tariff."""
    if user.is_superuser:
        return True

    if tariff.created_by_id == user.id:
        return True

    return any(
        is_pdc_allowed_for_user(id_pdc_itinerance, user)
        for id_pdc_itinerance in ids_pdc_itinerance
    )


def get_applicable_tariff_for_pdc(
    session: Session,
    id_pdc_itinerance: IdPdcItinerance,
    at: datetime,
) -> tuple[bool, Optional[Tariff]]:
    """Return the applicable tariff for an active charge point.

    The boolean indicates whether the charge point exists, so callers can keep
    separate error messages for unknown charge points and charge points without
    tariffs. The newest started tariff wins, even if it is expired; in that case
    no older tariff is returned.
    """
    stmt = (
        select(ActivePointsDeChargeView.id, Tariff)  # type: ignore[attr-defined]
        .outerjoin(
            PointDeChargeTariff,
            cast(SAColumn, PointDeChargeTariff.point_de_charge_id)
            == cast(
                SAColumn,
                ActivePointsDeChargeView.id,  # type: ignore[attr-defined]
            ),
        )
        .outerjoin(
            Tariff,
            and_(
                cast(SAColumn, Tariff.id)
                == cast(SAColumn, PointDeChargeTariff.tariff_id),
                cast(SAColumn, Tariff.deleted_at).is_(None),
                cast(SAColumn, Tariff.start) <= at,
            ),
        )
        .where(
            ActivePointsDeChargeView.id_pdc_itinerance  # type: ignore[attr-defined]
            == id_pdc_itinerance
        )
        .order_by(
            nullslast(desc(cast(SAColumn, Tariff.start))),
            nullslast(desc(cast(SAColumn, Tariff.original_last_updated))),
            nullslast(desc(cast(SAColumn, Tariff.created_at))),
        )
    )
    row = session.exec(stmt).first()
    if row is None:
        return False, None

    tariff = row[1]

    # No tariff exists for this charge point or it is outdated
    if tariff is None or (tariff.end is not None and tariff.end <= at):
        return True, None

    return True, tariff
