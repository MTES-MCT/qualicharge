"""QualiCharge API v1 tariff router."""

import datetime
import logging
from typing import Annotated, List, Optional, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Security
from fastapi import status as fa_status
from pydantic.types import AwareDatetime
from sqlalchemy import any_, func
from sqlalchemy.dialects.postgresql import array, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, select

from qualicharge.api.utils import GzipRoute, build_pagination_urls
from qualicharge.auth.oidc import get_user
from qualicharge.auth.schemas import ScopesEnum, User
from qualicharge.conf import settings
from qualicharge.db import get_session
from qualicharge.exceptions import PermissionDenied
from qualicharge.models.fields import IdPdcItinerance
from qualicharge.models.tariff import (
    PaginatedTariffListResponse,
    TariffChargePointUpdate,
    TariffCreate,
    TariffRead,
)
from qualicharge.schemas.core import (
    ActivePointsDeChargeView,
    PointDeCharge,
)
from qualicharge.schemas.tariff import PointDeChargeTariff, Tariff
from qualicharge.schemas.utils import (
    are_pdcs_allowed_for_user,
    get_applicable_tariff_for_pdc,
    get_tariff_pdc_ids,
    get_tariffs_pdc_ids,
    is_pdc_allowed_for_user,
    is_tariff_allowed_for_user,
)

logger = logging.getLogger(__name__)

type PdcDbIdsByItineranceId = dict[IdPdcItinerance, UUID]


router = APIRouter(
    prefix="/tariff",
    tags=["Tariff"],
    route_class=GzipRoute,
)


def _get_pdc_ids(
    ids_pdc_itinerance: set[IdPdcItinerance],
    session: Session,
) -> PdcDbIdsByItineranceId:
    """Get active charge point database ids by public itinerance identifiers."""
    if not ids_pdc_itinerance:
        return {}

    rows = session.exec(
        select(
            ActivePointsDeChargeView.id_pdc_itinerance,  # type: ignore[attr-defined]
            ActivePointsDeChargeView.id,  # type: ignore[attr-defined]
        ).where(
            cast(
                SAColumn,
                ActivePointsDeChargeView.id_pdc_itinerance,  # type: ignore[attr-defined]
            ).in_(ids_pdc_itinerance)
        )
    ).all()
    pdc_db_ids_by_itinerance_id: PdcDbIdsByItineranceId = dict(rows)
    if len(pdc_db_ids_by_itinerance_id) != len(ids_pdc_itinerance):
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail="Point of charge does not exist",
        )
    return pdc_db_ids_by_itinerance_id


def _get_tariff_or_404_for_user(
    tariff_id: UUID,
    user: User,
    session: Session,
) -> tuple[Tariff, list[IdPdcItinerance]]:
    """Get a tariff and its public charge point identifiers for a user."""
    stmt = (
        select(
            Tariff,
            PointDeCharge.id_pdc_itinerance,
        )
        .outerjoin(
            PointDeChargeTariff,
            cast(SAColumn, PointDeChargeTariff.tariff_id) == cast(SAColumn, Tariff.id),
        )
        .outerjoin(
            PointDeCharge,
            cast(SAColumn, PointDeCharge.id)
            == cast(SAColumn, PointDeChargeTariff.point_de_charge_id),
        )
        .where(
            Tariff.id == tariff_id,
            cast(SAColumn, Tariff.deleted_at).is_(None),
        )
    )
    rows = session.exec(stmt).all()
    if not rows:
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail="Tariff does not exist",
        )

    tariff = rows[0][0]
    ids_pdc_itinerance = [
        id_pdc_itinerance
        for _, id_pdc_itinerance in rows
        if id_pdc_itinerance is not None
    ]

    if not is_tariff_allowed_for_user(tariff, ids_pdc_itinerance, user):
        raise PermissionDenied("You cannot access this tariff")

    return tariff, ids_pdc_itinerance


def _add_tariff_associations(
    tariff: Tariff,
    ids_pdc_itinerance: set[IdPdcItinerance],
    user: User,
    session: Session,
) -> list[IdPdcItinerance]:
    """Associate a tariff with charge points.

    Return list[IdPdcItinerance] resolved from the database so callers can
    build responses without re-querying the association table.
    """
    if not ids_pdc_itinerance:
        return []

    if not are_pdcs_allowed_for_user(ids_pdc_itinerance, user):
        raise PermissionDenied("You cannot associate tariff with these charge points")

    pdc_db_ids_by_itinerance_id = _get_pdc_ids(
        ids_pdc_itinerance,
        session,
    )
    stmt = insert(PointDeChargeTariff).values(
        [
            {
                "point_de_charge_id": pdc_db_id,
                "tariff_id": tariff.id,
                "created_by_id": user.id,
                "updated_by_id": user.id,
            }
            for pdc_db_id in pdc_db_ids_by_itinerance_id.values()
        ]
    )
    session.exec(
        stmt.on_conflict_do_nothing(
            index_elements=["point_de_charge_id", "tariff_id"],
        )
    )
    return list(pdc_db_ids_by_itinerance_id.keys())


@router.get("/", response_model=PaginatedTariffListResponse)
async def list_tariffs(  # noqa: PLR0913
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_READ.value])],
    request: Request,
    from_: Annotated[
        Optional[AwareDatetime],
        Query(alias="from", title="Application date from"),
    ] = None,
    to: Annotated[
        Optional[AwareDatetime],
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
    original_id: Annotated[
        Optional[str],
        Query(description="Filter tariffs by original OCPI identifier"),
    ] = None,
    current: Annotated[
        Optional[bool],
        Query(description="Return only tariffs applicable at the current date"),
    ] = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=settings.API_STATIQUE_PAGE_SIZE, ge=0, le=1000),
    session: Session = Depends(get_session),
) -> PaginatedTariffListResponse:
    """List tariffs accessible to the current user."""
    stmt = select(Tariff).where(cast(SAColumn, Tariff.deleted_at).is_(None))

    if current:
        now = datetime.datetime.now(datetime.timezone.utc)
        from_ = now
        to = now

    if from_ is not None:
        stmt = stmt.where(
            cast(SAColumn, Tariff.end).is_(None) | (cast(SAColumn, Tariff.end) > from_)
        )
    if to is not None:
        stmt = stmt.where(cast(SAColumn, Tariff.start) <= to)

    if original_id is not None:
        stmt = stmt.where(Tariff.original_id == original_id)

    ou_filter: array | None = None
    if not user.is_superuser:
        # If user has no assigned operational units, we filter on an empty VARCHAR array
        ou_filter = array([f"{ou.code}%" for ou in user.operational_units] or [""])

    should_join_pdc = bool(pdc) or ou_filter is not None
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

    if ou_filter is not None:
        stmt = stmt.where(
            cast(
                SAColumn,
                ActivePointsDeChargeView.id_pdc_itinerance,  # type: ignore[attr-defined]
            ).like(any_(ou_filter))
        )

    total_statement = select(func.count()).select_from(
        stmt.with_only_columns(cast(SAColumn, Tariff.id)).distinct().subquery()
    )
    total = session.exec(total_statement).one()
    tariffs = session.exec(
        stmt.distinct()
        .order_by(cast(SAColumn, Tariff.created_at))
        .offset(offset)
        .limit(limit)
    ).all()
    pdc_ids_by_tariff_id = get_tariffs_pdc_ids(
        session,
        [tariff.id for tariff in tariffs],
    )
    items = [
        tariff.to_read(pdc_ids_by_tariff_id.get(tariff.id, [])) for tariff in tariffs
    ]

    previous_url, next_url = build_pagination_urls(
        request,
        offset,
        limit,
        total,
        len(items),
    )

    return PaginatedTariffListResponse(
        total=total,
        limit=limit,
        offset=offset,
        previous=previous_url,
        next=next_url,
        items=items,
    )


@router.post(
    "/",
    status_code=fa_status.HTTP_201_CREATED,
    response_model=TariffRead,
)
async def create(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_CREATE.value])],
    tariff: TariffCreate,
    session: Session = Depends(get_session),
) -> TariffRead:
    """Create a tariff and optionally associate it with charge points."""
    created_tariff: Tariff
    ids_pdc_itinerance: list[IdPdcItinerance]
    try:
        with session.begin_nested():
            raw = tariff.tariff.model_dump(by_alias=True, mode="json")
            created_tariff = Tariff(
                original_id=tariff.tariff.tariff_id,
                original_last_updated=tariff.tariff.last_updated,
                raw=raw,
                start=tariff.tariff.tariff_application_date,
                end=tariff.tariff.end_date_time,
                created_by_id=user.id,
                updated_by_id=user.id,
            )
            session.add(created_tariff)
            session.flush()
            ids_pdc_itinerance = _add_tariff_associations(
                created_tariff,
                set(tariff.targets),
                user,
                session,
            )
    except IntegrityError as err:
        raise HTTPException(
            status_code=fa_status.HTTP_409_CONFLICT,
            detail="Tariff already exists or cannot be associated",
        ) from err

    session.commit()
    session.refresh(created_tariff)
    return created_tariff.to_read(ids_pdc_itinerance)


@router.get("/{tariff_id}", response_model=TariffRead)
async def read(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_READ.value])],
    tariff_id: UUID,
    session: Session = Depends(get_session),
) -> TariffRead:
    """Read a tariff by its QualiCharge UUID."""
    tariff, ids_pdc_itinerance = _get_tariff_or_404_for_user(
        tariff_id,
        user,
        session,
    )
    return tariff.to_read(ids_pdc_itinerance)


@router.get("/{id_pdc_itinerance}/applicable", response_model=TariffRead)
async def read_applicable(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_READ.value])],
    id_pdc_itinerance: Annotated[str, Path()],
    at: Optional[AwareDatetime] = Query(default=None),
    session: Session = Depends(get_session),
) -> TariffRead:
    """Read applicable tariff for a charge point."""
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You cannot read tariff for this point of charge")

    if at is None:
        at = datetime.datetime.now(datetime.timezone.utc)
    pdc_exists, tariff = get_applicable_tariff_for_pdc(
        session,
        id_pdc_itinerance,
        at,
    )
    if not pdc_exists:
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail="Point of charge does not exist",
        )
    if tariff is None:
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail="Selected point of charge does not have tariff record yet",
        )
    return tariff.to_read(get_tariff_pdc_ids(session, tariff))


@router.put("/chargepoint/{id_pdc_itinerance}", response_model=TariffRead)
async def apply_tariff(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_UPDATE.value])],
    id_pdc_itinerance: Annotated[str, Path()],
    payload: TariffChargePointUpdate,
    session: Session = Depends(get_session),
) -> TariffRead:
    """Apply an existing tariff to a charge point."""
    tariff, _ = _get_tariff_or_404_for_user(payload.tariff_id, user, session)

    try:
        with session.begin_nested():
            _add_tariff_associations(
                tariff,
                {id_pdc_itinerance},
                user,
                session,
            )
    except IntegrityError as err:
        raise HTTPException(
            status_code=fa_status.HTTP_409_CONFLICT,
            detail="Tariff cannot be associated",
        ) from err

    session.commit()
    session.refresh(tariff)
    return tariff.to_read(get_tariff_pdc_ids(session, tariff))
