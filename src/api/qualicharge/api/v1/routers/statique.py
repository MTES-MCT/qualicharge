"""QualiCharge API v1 statique router."""

import logging
from typing import Annotated, List

from annotated_types import Len
from fastapi import APIRouter, status
from pydantic import BaseModel, computed_field

from qualicharge.conf import settings
from qualicharge.factories.static import StatiqueFactory
from qualicharge.models.static import Statique

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/statique",
    tags=["IRVE Statique schema"],
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
    telephone_operateur = "0123456789"
    id_station_itinerance = "ESZUNP8891687432127666088"
    id_pdc_itinerance = "ESZUNE1111ER1"

    return StatiqueFactory.batch(
        size=10,
        telephone_operateur=telephone_operateur,
        id_station_itinerance=id_station_itinerance,
        id_pdc_itinerance=id_pdc_itinerance,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(statique: Statique) -> StatiqueItemsCreatedResponse:
    """Create a statique item."""
    return StatiqueItemsCreatedResponse(items=[statique])


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk(statiques: BulkStatiqueList) -> StatiqueItemsCreatedResponse:
    """Create a set of statique items."""
    return StatiqueItemsCreatedResponse(items=statiques)
