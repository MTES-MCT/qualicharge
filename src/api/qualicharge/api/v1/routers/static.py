"""QualiCharge API v1 statique router."""

import logging
from typing import Annotated, List, Optional, cast

from annotated_types import Len
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from pydantic import AnyHttpUrl, BaseModel, computed_field
from sqlalchemy import func
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, select

from qualicharge.conf import settings
from qualicharge.db import get_session
from qualicharge.exceptions import IntegrityError, ObjectDoesNotExist
from qualicharge.models.static import Statique
from qualicharge.schemas import PointDeCharge
from qualicharge.schemas.utils import (
    build_statique,
    list_statique,
    save_statique,
    save_statiques,
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
    items: List[Statique]

    @computed_field  # type: ignore[misc]
    @property
    def size(self) -> int:
        """The number of items created."""
        return len(self.items)


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
    request: Request,
    offset: int = 0,
    limit: int = Query(
        default=settings.API_STATIQUE_BULK_CREATE_MAX_SIZE,
        le=settings.API_STATIQUE_BULK_CREATE_MAX_SIZE,
    ),
    session: Session = Depends(get_session),
) -> PaginatedStatiqueListResponse:
    """List statique items."""
    current_url = request.url
    previous_url = next_url = None
    total = session.exec(select(func.count(cast(SAColumn, PointDeCharge.id)))).one()
    statiques = [statique for statique in list_statique(session, offset, limit)]

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
    try:
        update = update_statique(session, id_pdc_itinerance, statique)
    except IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="id_pdc_itinerance does not match request body",
        ) from err
    except ObjectDoesNotExist as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statique to update does not exist",
        ) from err
    return update


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(
    statique: Statique, session: Session = Depends(get_session)
) -> StatiqueItemsCreatedResponse:
    """Create a statique item."""
    return StatiqueItemsCreatedResponse(items=[save_statique(session, statique)])


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk(
    statiques: BulkStatiqueList, session: Session = Depends(get_session)
) -> StatiqueItemsCreatedResponse:
    """Create a set of statique items."""
    statiques = [statique for statique in save_statiques(session, statiques)]
    if not len(statiques):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All Statique entries already exist",
        )
    return StatiqueItemsCreatedResponse(items=statiques)
