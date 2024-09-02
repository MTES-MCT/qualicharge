"""QualiCharge API v1 statique router."""

import logging
from io import StringIO
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
from psycopg import Error as PGError
from pydantic import AnyHttpUrl, BaseModel, computed_field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, select

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
from qualicharge.schemas.core import OperationalUnit, PointDeCharge, Station
from qualicharge.schemas.sql import StatiqueImporter
from qualicharge.schemas.utils import (
    build_statique,
    is_pdc_allowed_for_user,
    list_statique,
    save_statique,
    update_statique,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/statique",
    tags=["IRVE Statique"],
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
    List[Statique], Len(2, settings.API_STATIQUE_BULK_CREATE_MAX_SIZE)
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
    """List statique items."""
    current_url = request.url
    previous_url = next_url = None
    total_statement = select(func.count(cast(SAColumn, PointDeCharge.id)))
    operational_units = None
    if not user.is_superuser:
        operational_units = user.operational_units
        total_statement = (
            total_statement.join_from(
                PointDeCharge,
                Station,
                PointDeCharge.station_id == Station.id,  # type: ignore[arg-type]
            )
            .join_from(
                Station,
                OperationalUnit,
                Station.operational_unit_id == OperationalUnit.id,  # type: ignore[arg-type]
            )
            .where(
                cast(SAColumn, OperationalUnit.id).in_(
                    ou.id for ou in user.operational_units
                )
            )
        )
    total = session.exec(total_statement).one()
    statiques = [
        statique
        for statique in list_statique(session, offset, limit, operational_units)
    ]

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
    """Read statique item (point de charge)."""
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You don't manage this point of charge")

    try:
        statique = build_statique(session, id_pdc_itinerance)
    except ObjectDoesNotExist as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested statique does not exist",
        ) from err
    return statique


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
        raise PermissionDenied("You don't manage this point of charge")

    transaction = session.begin_nested()
    try:
        update = update_statique(session, id_pdc_itinerance, statique)
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

    transaction = session.begin_nested()
    try:
        db_statique = save_statique(session, statique)
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
    """Create a set of statique items."""
    for statique in statiques:
        if not is_pdc_allowed_for_user(statique.id_pdc_itinerance, user):
            raise PermissionDenied(
                "You cannot submit data for an organization you are not assigned to"
            )

    # Convert statiques to a Pandas DataFrame
    df = pd.read_json(
        StringIO(f"{'\n'.join([s.model_dump_json() for s in statiques])}"),
        lines=True,
        dtype_backend="pyarrow",
    )

    importer = StatiqueImporter(df, session.connection())
    transaction = session.begin_nested()
    try:
        importer.save()
        transaction.commit()
    except (
        ProgrammingError,
        IntegrityError,
        OperationalError,
        PGError,
        ObjectDoesNotExist,
    ) as err:
        transaction.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        ) from err

    return StatiqueItemsCreatedResponse(items=df["id_pdc_itinerance"])
