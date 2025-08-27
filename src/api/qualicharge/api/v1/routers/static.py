"""QualiCharge API v1 statique router."""

import datetime
import logging
from io import BytesIO
from typing import Annotated, List, Optional, cast

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
    NoResultFound,
)
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, select

from qualicharge.api.utils import GzipRoute
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
from qualicharge.schemas.core import LatestStatus, PointDeCharge, StatiqueMV
from qualicharge.schemas.sql import StatiqueImporter
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


class PaginatedStatiqueListResponse(BaseModel):
    """Paginated statique list response."""

    limit: int
    offset: int
    total: int
    previous: Optional[AnyHttpUrl]
    next: Optional[AnyHttpUrl]
    items: List[Statique]

    @computed_field  # type: ignore[misc]
    @property
    def size(self) -> int:
        """The number of items created."""
        return len(self.items)


BulkStatiqueList = Annotated[
    List[Statique], Len(1, settings.API_STATIQUE_BULK_CREATE_MAX_SIZE)
]


@router.get("/")
async def list(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.STATIC_READ.value])],
    request: Request,
    offset: int = 0,
    limit: int = Query(
        default=settings.API_STATIQUE_PAGE_SIZE,
        le=settings.API_STATIQUE_PAGE_MAX_SIZE,
    ),
    session: Session = Depends(get_session),
) -> PaginatedStatiqueListResponse:
    """List statique items.

    Note that it can take up to 10 minutes for a created Statique item to appear in
    this endpoint response.
    """
    current_url = request.url
    previous_url = next_url = None

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
    try:
        statiques = [
            Statique(**s.model_dump(exclude={"pdc_id", "pdc_updated_at"}))
            for s in session.exec(statement).all()
        ]
    except ValidationError as err:
        raise HTTPException(
            status_code=422,
            detail="Statique data is no longer valid, please update those first",
        ) from err

    previous_offset = offset - limit if offset > limit else 0
    if offset:
        previous_url = str(current_url.include_query_params(offset=previous_offset))

    if not limit > len(statiques) and total != offset + limit:
        next_url = str(current_url.include_query_params(offset=offset + limit))

    return PaginatedStatiqueListResponse(
        total=total,
        limit=limit,
        offset=offset,
        previous=previous_url,
        next=next_url,
        items=statiques,
    )


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
        raise HTTPException(
            status_code=422,
            detail="Statique data is no longer valid, please update it first",
        ) from err


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
    if all(p.deleted_at is None for p in station.points_de_charge):
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
