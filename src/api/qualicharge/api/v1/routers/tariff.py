"""QualiCharge API v1 tariff router."""

import datetime as dt
from datetime import datetime
from typing import Annotated, List, Optional, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Security
from fastapi import status as fa_status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, select

from qualicharge.api.v1.routers.dynamic import get_pdc_id
from qualicharge.auth.oidc import get_user
from qualicharge.auth.schemas import ScopesEnum, User
from qualicharge.db import get_session
from qualicharge.exceptions import PermissionDenied
from qualicharge.models.tariff import (
    PointDeChargeTariffCreate,
    TariffCreate,
    TariffRead,
)
from qualicharge.schemas.core import ActivePointsDeChargeView, ActiveStationsView
from qualicharge.schemas.tariff import PointDeChargeTariff, Tariff
from qualicharge.schemas.tariff_utils import (
    get_applicable_tariff,
    get_tariff_by_original,
    is_tariff_allowed_for_user,
    tariff_fields_from_object,
    tariff_to_read,
    to_db_datetime,
)
from qualicharge.schemas.utils import are_pdcs_allowed_for_user, is_pdc_allowed_for_user

router = APIRouter(prefix="/statique", tags=["Tariff"])


def _get_tariff_or_404(
    tariff_id: UUID,
    session: Session,
    include_deleted: bool = False,
) -> Tariff:
    """Get a tariff by id or raise a 404 error."""
    stmt = select(Tariff).where(Tariff.id == tariff_id)
    if not include_deleted:
        stmt = stmt.where(cast(SAColumn, Tariff.deleted_at).is_(None))
    tariff = session.exec(stmt).one_or_none()
    if tariff is None:
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail="Tariff does not exist",
        )
    return tariff


def _ensure_tariff_allowed(tariff: Tariff, user: User, session: Session) -> None:
    """Raise if a user cannot access a tariff."""
    if not is_tariff_allowed_for_user(session, tariff.id, user):
        raise PermissionDenied("You cannot access this tariff")


def _add_tariff_associations(
    tariff: Tariff,
    ids_pdc_itinerance: set[str],
    user: User,
    session: Session,
) -> None:
    """Associate a tariff with charge points."""
    if not ids_pdc_itinerance:
        return

    if not are_pdcs_allowed_for_user(ids_pdc_itinerance, user):
        raise PermissionDenied("You cannot associate tariff with these charge points")

    for id_pdc_itinerance in ids_pdc_itinerance:
        pdc_id = get_pdc_id(id_pdc_itinerance, session)
        association = session.exec(
            select(PointDeChargeTariff).where(
                PointDeChargeTariff.point_de_charge_id == pdc_id,
                PointDeChargeTariff.tariff_id == tariff.id,
            )
        ).one_or_none()
        if association is not None:
            continue

        session.add(
            PointDeChargeTariff(
                point_de_charge_id=pdc_id,
                tariff_id=tariff.id,
                created_by_id=user.id,
                updated_by_id=user.id,
            )
        )


@router.get("/tariff/", response_model=List[TariffRead])
async def list_tariffs(  # noqa: PLR0913
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_READ.value])],
    from_: Annotated[
        Optional[datetime],
        Query(alias="from", title="Application date from"),
    ] = None,
    to: Annotated[
        Optional[datetime],
        Query(title="Application date to"),
    ] = None,
    pdc: Annotated[
        Optional[List[str]],
        Query(
            title="Point de charge",
            description=(
                "Filter tariffs by `id_pdc_itinerance` "
                "(can be provided multiple times)"
            ),
        ),
    ] = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0, le=1000),
    session: Session = Depends(get_session),
) -> List[TariffRead]:
    """List tariffs accessible to the current user."""
    stmt = select(Tariff).where(cast(SAColumn, Tariff.deleted_at).is_(None))
    from_ = to_db_datetime(from_)
    to = to_db_datetime(to)

    if from_ is not None:
        stmt = stmt.where(
            cast(SAColumn, Tariff.end).is_(None) | (cast(SAColumn, Tariff.end) >= from_)
        )
    if to is not None:
        stmt = stmt.where(
            cast(SAColumn, Tariff.start).is_(None)
            | (cast(SAColumn, Tariff.start) <= to)
        )

    should_join_pdc = bool(pdc) or not user.is_superuser
    if should_join_pdc:
        stmt = stmt.join(
            PointDeChargeTariff,
            cast(SAColumn, PointDeChargeTariff.tariff_id) == cast(SAColumn, Tariff.id),
        ).join(
            ActivePointsDeChargeView,
            cast(SAColumn, PointDeChargeTariff.point_de_charge_id)
            == cast(SAColumn, ActivePointsDeChargeView.id),  # type: ignore[attr-defined]
        )

    if pdc:
        stmt = stmt.where(
            cast(
                SAColumn,
                ActivePointsDeChargeView.id_pdc_itinerance,  # type: ignore[attr-defined]
            ).in_(pdc)
        )

    if not user.is_superuser:
        stmt = stmt.join(
            ActiveStationsView,
            ActivePointsDeChargeView.station_id  # type: ignore[attr-defined]
            == ActiveStationsView.id,  # type: ignore[attr-defined]
        )
        ou_ids = [ou.id for ou in user.operational_units]
        stmt = stmt.where(
            cast(
                SAColumn,
                ActiveStationsView.operational_unit_id,  # type: ignore[attr-defined]
            ).in_(ou_ids)
        )

    tariffs = session.exec(
        stmt.distinct()
        .order_by(cast(SAColumn, Tariff.created_at))
        .offset(offset)
        .limit(limit)
    ).all()
    return [tariff_to_read(session, tariff) for tariff in tariffs]


@router.post(
    "/tariff/",
    status_code=fa_status.HTTP_201_CREATED,
    response_model=TariffRead,
)
async def create_tariff(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_CREATE.value])],
    payload: TariffCreate,
    session: Session = Depends(get_session),
) -> TariffRead:
    """Create a tariff and optionally associate it with charge points."""
    pdc_ids = set(payload.id_pdc_itinerance)
    if get_tariff_by_original(
        session, payload.tariff.tariff_id, payload.tariff.last_updated
    ):
        raise HTTPException(
            status_code=fa_status.HTTP_409_CONFLICT,
            detail="Tariff with same original id and last update already exists",
        )

    tariff = Tariff(
        **tariff_fields_from_object(payload.tariff),
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    transaction = session.begin_nested()
    try:
        session.add(tariff)
        session.flush()
        _add_tariff_associations(tariff, pdc_ids, user, session)
    except IntegrityError as err:
        transaction.rollback()
        raise HTTPException(
            status_code=fa_status.HTTP_409_CONFLICT,
            detail="Tariff already exists or cannot be associated",
        ) from err

    session.commit()
    session.refresh(tariff)
    return tariff_to_read(session, tariff)


@router.get("/tariff/{id}", response_model=TariffRead)
async def read_tariff(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_READ.value])],
    id: UUID,
    session: Session = Depends(get_session),
) -> TariffRead:
    """Read a tariff by its QualiCharge UUID."""
    tariff = _get_tariff_or_404(id, session)
    _ensure_tariff_allowed(tariff, user, session)
    return tariff_to_read(session, tariff)


@router.delete("/tariff/{id}", status_code=fa_status.HTTP_204_NO_CONTENT)
async def delete_tariff(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_DELETE.value])],
    id: UUID,
    session: Session = Depends(get_session),
) -> None:
    """Soft-delete a tariff."""
    tariff = _get_tariff_or_404(id, session)
    _ensure_tariff_allowed(tariff, user, session)

    now = dt.datetime.now(dt.timezone.utc)
    tariff.deleted_at = now
    tariff.deleted_by_id = user.id
    tariff.updated_by_id = user.id
    session.add(tariff)
    session.commit()


@router.get("/{id_pdc_itinerance}/tariff", response_model=TariffRead)
async def read_applicable_tariff(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_READ.value])],
    id_pdc_itinerance: Annotated[str, Path()],
    at: Optional[datetime] = Query(default=None),
    session: Session = Depends(get_session),
) -> TariffRead:
    """Read applicable tariff for a charge point."""
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You cannot read tariff for this point of charge")

    pdc_id = get_pdc_id(id_pdc_itinerance, session)
    if at is None:
        at = dt.datetime.now(dt.timezone.utc)
    at = to_db_datetime(at)
    if at is None:
        raise HTTPException(
            status_code=fa_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid tariff application datetime",
        )
    tariff = get_applicable_tariff(session, pdc_id, at)
    if tariff is None:
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail="Selected point of charge does not have tariff record yet",
        )
    return tariff_to_read(session, tariff)


@router.post("/pointdechargetariff", response_model=TariffRead)
async def associate_tariff_with_points_de_charge(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_UPDATE.value])],
    payload: PointDeChargeTariffCreate,
    session: Session = Depends(get_session),
) -> TariffRead:
    """Associate an existing tariff with charge points."""
    tariff = get_tariff_by_original(
        session, payload.original_id, payload.original_last_updated
    )
    if tariff is None:
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail="Tariff does not exist",
        )

    _ensure_tariff_allowed(tariff, user, session)
    transaction = session.begin_nested()
    try:
        _add_tariff_associations(tariff, set(payload.id_pdc_itinerance), user, session)
    except IntegrityError as err:
        transaction.rollback()
        raise HTTPException(
            status_code=fa_status.HTTP_409_CONFLICT,
            detail="Tariff cannot be associated with selected charge points",
        ) from err

    tariff.updated_by_id = user.id
    session.add(tariff)
    session.commit()
    session.refresh(tariff)
    return tariff_to_read(session, tariff)
