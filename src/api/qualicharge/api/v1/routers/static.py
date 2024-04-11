"""QualiCharge API v1 statique router."""

import logging
from typing import Annotated, List

from annotated_types import Len
from fastapi import APIRouter, Path, status
from pydantic import BaseModel, computed_field

from qualicharge.conf import settings
from qualicharge.models.static import Statique

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


BulkStatiqueList = Annotated[List[Statique], Len(2, settings.API_BULK_CREATE_MAX_SIZE)]


@router.get("/")
async def list() -> List[Statique]:
    """List statique items."""
    return []


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
) -> Statique:
    """Read statique item (point de charge)."""
    raise NotImplementedError


@router.put("/{id_pdc_itinerance}")
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
) -> Statique:
    """Update statique item (point de charge)."""
    raise NotImplementedError


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(statique: Statique) -> StatiqueItemsCreatedResponse:
    """Create a statique item."""
    return StatiqueItemsCreatedResponse(items=[statique])


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk(statiques: BulkStatiqueList) -> StatiqueItemsCreatedResponse:
    """Create a set of statique items."""
    return StatiqueItemsCreatedResponse(items=statiques)
