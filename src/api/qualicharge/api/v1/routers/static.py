"""QualiCharge API v1 statique router."""

import datetime
import json
import logging
from io import BytesIO
from typing import Annotated, Generic, List, Optional, TypeVar, cast
from uuid import UUID

import pandas as pd
from annotated_types import Len
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Security,
    status,
)
from pydantic import AnyHttpUrl, BaseModel, ValidationError, computed_field
from sqlalchemy import any_, func
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.exc import (
    IntegrityError,
    NoResultFound,
)
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, select

from qualicharge.api.utils import GzipRoute
from qualicharge.api.v1.routers.dynamic import get_pdc_id
from qualicharge.auth.oidc import get_user
from qualicharge.auth.schemas import ScopesEnum, User
from qualicharge.conf import settings
from qualicharge.db import get_session
from qualicharge.exceptions import (
    IntegrityError as QCIntegrityError,
)
from qualicharge.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied,
)
from qualicharge.models.static import Statique
from qualicharge.models.tariff import TariffCreate, TariffRead
from qualicharge.schemas.core import (
    ActivePointsDeChargeView,
    ActiveStationsView,
    LatestStatus,
    PointDeCharge,
    StatiqueMV,
)
from qualicharge.schemas.sql import StatiqueImporter
from qualicharge.schemas.tariff import PointDeChargeTariff, Tariff
from qualicharge.schemas.tariff_utils import (
    get_applicable_tariff,
    get_tariff_by_original,
    is_tariff_allowed_for_user,
    tariff_fields_from_object,
    tariff_to_read,
    to_db_datetime,
)
from qualicharge.schemas.utils import (
    are_pdcs_allowed_for_user,
    is_pdc_allowed_for_user,
    save_statique,
    update_statique,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/statique",
    tags=["IRVE Statique"],
    route_class=GzipRoute,
)

T = TypeVar("T")


class StatiqueItemsCreatedResponse(BaseModel):
    """API response model used when Statique items are created."""

    message: str = "Statique items created"
    items: List[str]

    @computed_field  # type: ignore[misc]
    @property
    def size(self) -> int:
        """The number of items created."""
        return len(self.items)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Statique items created",
                    "items": ["FRFASE3300401", "FRFASE3300402", "FRFASE3300403"],
                    "size": 3,
                }
            ]
        }
    }


class PaginatedListResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    limit: int
    offset: int
    total: int
    previous: Optional[AnyHttpUrl]
    next: Optional[AnyHttpUrl]
    items: List[T]

    @computed_field  # type: ignore[misc]
    @property
    def size(self) -> int:
        """The number of items returned."""
        return len(self.items)


class PaginatedStatiqueListResponse(PaginatedListResponse[Statique]):
    """Paginated statique list response."""


class PaginatedTariffListResponse(PaginatedListResponse[TariffRead]):
    """Paginated tariff list response."""


BulkStatiqueList = Annotated[
    List[Statique], Len(1, settings.API_STATIQUE_BULK_CREATE_MAX_SIZE)
]


def build_pagination_urls(
    request: Request,
    offset: int,
    limit: int,
    total: int,
    count: int,
) -> tuple[str | None, str | None]:
    """Build previous and next pagination URLs for a paginated response."""
    previous_url = next_url = None
    current_url = request.url

    previous_offset = offset - limit if offset > limit else 0
    if offset:
        previous_url = str(current_url.include_query_params(offset=previous_offset))

    if limit and count == limit and total > offset + limit:
        next_url = str(current_url.include_query_params(offset=offset + limit))

    return previous_url, next_url


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
            status_code=status.HTTP_404_NOT_FOUND,
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


@router.get("/")
async def list(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.STATIC_READ.value])],
    request: Request,
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=settings.API_STATIQUE_PAGE_SIZE,
        le=settings.API_STATIQUE_PAGE_MAX_SIZE,
        ge=0,
    ),
    session: Session = Depends(get_session),
) -> PaginatedStatiqueListResponse:
    """List statique items.

    Note that it can take up to 10 minutes for a created Statique item to appear in
    this endpoint response.
    """
    total_statement = select(func.count(cast(SAColumn, StatiqueMV.pdc_id)))

    ou_filter: array | None = None
    if not user.is_superuser:
        # If user has no assigned operational units, we filter on an empty VARCHAR array
        ou_filter = array([f"{ou.code}%" for ou in user.operational_units] or [""])

    if ou_filter is not None:
        total_statement = total_statement.where(
            cast(SAColumn, StatiqueMV.id_pdc_itinerance).like(any_(ou_filter))
        )
    total = session.exec(total_statement).one()

    statement = select(StatiqueMV)
    if ou_filter is not None:
        statement = statement.where(
            cast(SAColumn, StatiqueMV.id_pdc_itinerance).like(any_(ou_filter))
        )
    statement = (
        statement.order_by(StatiqueMV.id_pdc_itinerance).offset(offset).limit(limit)
    )
    # Provide detailled errors for each record in this page
    statiques = []
    errors = []
    for s in session.exec(statement).all():
        try:
            statiques.append(
                Statique(**s.model_dump(exclude={"pdc_id", "pdc_updated_at"}))
            )
        except ValidationError as err:
            errors.append(
                {
                    "id_pdc_itinerance": s.id_pdc_itinerance,
                    "errors": json.loads(err.json()),
                }
            )
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    previous_url, next_url = build_pagination_urls(
        request,
        offset,
        limit,
        total,
        len(statiques),
    )

    return PaginatedStatiqueListResponse(
        total=total,
        limit=limit,
        offset=offset,
        previous=previous_url,
        next=next_url,
        items=statiques,
    )


@router.get("/tariff/", response_model=PaginatedTariffListResponse)
async def list_tariffs(  # noqa: PLR0913
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_READ.value])],
    request: Request,
    from_: Annotated[
        Optional[datetime.datetime],
        Query(alias="from", title="Application date from"),
    ] = None,
    to: Annotated[
        Optional[datetime.datetime],
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

    from_ = to_db_datetime(from_)
    to = to_db_datetime(to)
    if current:
        now = to_db_datetime(datetime.datetime.now(datetime.timezone.utc))
        from_ = now
        to = now

    if from_ is not None:
        stmt = stmt.where(
            cast(SAColumn, Tariff.end).is_(None) | (cast(SAColumn, Tariff.end) > from_)
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
        stmt = stmt.where(
            cast(
                SAColumn,
                ActiveStationsView.operational_unit_id,  # type: ignore[attr-defined]
            ).in_([ou.id for ou in user.operational_units])
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
    items = [tariff_to_read(session, tariff) for tariff in tariffs]

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
    "/tariff/",
    status_code=status.HTTP_201_CREATED,
    response_model=TariffRead,
)
async def create_tariff(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_CREATE.value])],
    payload: TariffCreate,
    session: Session = Depends(get_session),
) -> TariffRead:
    """Create a tariff and optionally associate it with charge points."""
    targets = set(payload.targets)
    if get_tariff_by_original(
        session,
        payload.tariff.tariff_id,
        payload.tariff.last_updated,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
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
        _add_tariff_associations(tariff, targets, user, session)
    except IntegrityError as err:
        transaction.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
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


@router.get("/{id_pdc_itinerance}/tariff", response_model=TariffRead)
async def read_applicable_tariff(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_READ.value])],
    id_pdc_itinerance: Annotated[str, Path()],
    at: Optional[datetime.datetime] = Query(default=None),
    session: Session = Depends(get_session),
) -> TariffRead:
    """Read applicable tariff for a charge point."""
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You cannot read tariff for this point of charge")

    pdc_id = get_pdc_id(id_pdc_itinerance, session)
    if at is None:
        at = datetime.datetime.now(datetime.timezone.utc)
    at = to_db_datetime(at)
    if at is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid tariff application datetime",
        )
    tariff = get_applicable_tariff(session, pdc_id, at)
    if tariff is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected point of charge does not have tariff record yet",
        )
    return tariff_to_read(session, tariff)


@router.put("/{id_pdc_itinerance}/tariff/{tariff_id}", response_model=TariffRead)
async def apply_tariff(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.TARIFF_UPDATE.value])],
    id_pdc_itinerance: Annotated[str, Path()],
    tariff_id: UUID,
    session: Session = Depends(get_session),
) -> TariffRead:
    """Apply an existing tariff to a charge point."""
    tariff = _get_tariff_or_404(tariff_id, session)

    transaction = session.begin_nested()
    try:
        _add_tariff_associations(tariff, {id_pdc_itinerance}, user, session)
    except ObjectDoesNotExist as err:
        transaction.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except IntegrityError as err:
        transaction.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tariff cannot be associated",
        ) from err

    session.commit()
    session.refresh(tariff)
    return tariff_to_read(session, tariff)


@router.get("/{id_pdc_itinerance}")
async def read(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.STATIC_READ.value])],
    id_pdc_itinerance: Annotated[
        str,
        Path(
            description=(
                "L'identifiant du point de recharge délivré selon les modalités "
                "définies à l'article 10 du décret n° 2017-26 du 12 janvier 2017."
            ),
        ),
    ],
    session: Session = Depends(get_session),
) -> Statique:
    """Read statique item (point de charge).

    Note that it can take up to 10 minutes for a created Statique item to appear in
    this endpoint response.
    """
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You don't manage this charge point")

    try:
        statique_mv = session.exec(
            select(StatiqueMV).where(StatiqueMV.id_pdc_itinerance == id_pdc_itinerance)
        ).one()
    except NoResultFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Requested statique does not exist yet. You should wait up to "
                "10 minutes for a newly created entry."
            ),
        ) from err
    try:
        return Statique(**statique_mv.model_dump(exclude={"pdc_id", "pdc_updated_at"}))
    except ValidationError as err:
        raise HTTPException(status_code=422, detail=json.loads(err.json())) from err


@router.put("/{id_pdc_itinerance}", status_code=status.HTTP_200_OK)
async def update(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.STATIC_UPDATE.value])],
    id_pdc_itinerance: Annotated[
        str,
        Path(
            description=(
                "L'identifiant du point de recharge délivré selon les modalités "
                "définies à l'article 10 du décret n° 2017-26 du 12 janvier 2017."
            ),
        ),
    ],
    statique: Statique,
    session: Session = Depends(get_session),
) -> Statique:
    """Update statique item (point de charge)."""
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You don't manage this charge point")

    transaction = session.begin_nested()
    try:
        update = update_statique(
            session, id_pdc_itinerance, statique, author=user, only_active=True
        )
    except QCIntegrityError as err:
        transaction.rollback()
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="id_pdc_itinerance does not match request body",
        ) from err
    except ObjectDoesNotExist as err:
        transaction.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        ) from err

    # Commit changes
    session.commit()

    return update


@router.delete("/{id_pdc_itinerance}", status_code=status.HTTP_204_NO_CONTENT)
async def decommission(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.STATIC_DELETE.value])],
    id_pdc_itinerance: Annotated[
        str,
        Path(
            description=(
                "L'identifiant du point de recharge délivré selon les modalités "
                "définies à l'article 10 du décret n° 2017-26 du 12 janvier 2017."
            ),
        ),
    ],
    session: Session = Depends(get_session),
) -> None:
    """Decommission a charge point (point de charge).

    To decommission a charge point, your account should include the `static:delete`
    scope. If not, we invite you to contact an administrator to extend your permissions.

    If all charge points of a station have been decommissioned, the station will also be
    decommissioned.

    Note that decommissioning a charge point (or a station) does not delete concerned
    charge point (or station) nor related object in database, it is soft-deleted
    instead. You can recommission a charge point (and related station) using the
    dedicated API endpoint.

    Decommissioning an already decommissioned charge point has no effect.
    """
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You don't manage this charge point")

    # Get charge point
    poc = session.exec(
        select(PointDeCharge).where(
            PointDeCharge.id_pdc_itinerance == id_pdc_itinerance
        )
    ).one_or_none()
    if poc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target charge point does not exist",
        )

    # If the charge point has already been decommissioned, it should have no effect
    if poc.deleted_at is not None:
        return

    # Soft-delete the charge point
    now = datetime.datetime.now(datetime.timezone.utc)
    poc.deleted_at = now
    session.add(poc)

    # Should we also decommission the station?
    station = poc.station
    if all(p.deleted_at is not None for p in station.points_de_charge):
        station.deleted_at = now
        session.add(station)

    # Delete the latest status entry
    latest_status = session.exec(
        select(LatestStatus).where(LatestStatus.id_pdc_itinerance == id_pdc_itinerance)
    ).one_or_none()
    if latest_status:
        session.delete(latest_status)

    # Commit changes
    session.commit()


@router.post("/{id_pdc_itinerance}/up", status_code=status.HTTP_204_NO_CONTENT)
async def recommission(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.STATIC_DELETE.value])],
    id_pdc_itinerance: Annotated[
        str,
        Path(
            description=(
                "L'identifiant du point de recharge délivré selon les modalités "
                "définies à l'article 10 du décret n° 2017-26 du 12 janvier 2017."
            ),
        ),
    ],
    session: Session = Depends(get_session),
) -> None:
    """Recommission a charge point (point de charge).

    If all charge points of a station are decommissioned and you recommission one of its
    charge points, the station will also be recommissioned.
    """
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You don't manage this charge point")

    # Get charge point
    poc = session.exec(
        select(PointDeCharge).where(
            PointDeCharge.id_pdc_itinerance == id_pdc_itinerance
        )
    ).one_or_none()
    if poc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target charge point does not exist",
        )

    # The charge point is already active, ignore this request
    if poc.deleted_at is None:
        return

    # Reactivate the charge point
    poc.deleted_at = None
    session.add(poc)

    # Should we also recommission the station?
    station = poc.station
    if any(p.deleted_at is None for p in station.points_de_charge):
        station.deleted_at = None
        session.add(station)

    # Commit changes
    session.commit()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.STATIC_CREATE.value])],
    statique: Statique,
    session: Session = Depends(get_session),
) -> StatiqueItemsCreatedResponse:
    """Create a statique item."""
    if not is_pdc_allowed_for_user(statique.id_pdc_itinerance, user):
        raise PermissionDenied(
            "You cannot submit data for an organization you are not assigned to"
        )

    # Check if the charge point does not already exist
    if (
        session.exec(
            select(func.count(cast(SAColumn, PointDeCharge.id))).where(
                PointDeCharge.id_pdc_itinerance == statique.id_pdc_itinerance
            )
        ).one()
        > 0
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Charge point {statique.id_pdc_itinerance} already exists",
        )

    transaction = session.begin_nested()
    try:
        db_statique = save_statique(session, statique, author=user)
    except ObjectDoesNotExist as err:
        transaction.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        ) from err

    # Commit changes
    session.commit()

    return StatiqueItemsCreatedResponse(items=[db_statique.id_pdc_itinerance])


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.STATIC_CREATE.value])],
    statiques: BulkStatiqueList,
    session: Session = Depends(get_session),
) -> StatiqueItemsCreatedResponse:
    """Create or update a set of statique items.

    If an error occurs during batch importation, the database session is rolled
    back, hence none of the submitted statique is saved.
    """
    if not are_pdcs_allowed_for_user([s.id_pdc_itinerance for s in statiques], user):
        raise PermissionDenied(
            "You cannot submit data for an organization you are not assigned to"
        )

    # Convert statiques to a Pandas DataFrame
    df = pd.read_json(
        BytesIO(
            bytes(f"{'\n'.join([s.model_dump_json() for s in statiques])}", "utf-8")
        ),
        lines=True,
        orient="records",
        engine="pyarrow",
        dtype_backend="pyarrow",
    )

    transaction = session.begin_nested()
    importer = StatiqueImporter(df, transaction.session.connection(), author=user)
    try:
        importer.save()
    except QCIntegrityError as err:
        transaction.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
        ) from err
    except ObjectDoesNotExist as err:
        transaction.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        ) from err

    # Commit changes
    session.commit()

    return StatiqueItemsCreatedResponse(items=df["id_pdc_itinerance"])
