"""QualiCharge API v1 dynamique router."""

import logging
from typing import Annotated, List

from fastapi import APIRouter, Path, status

from qualicharge.models.dynamic import Status

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dynamique",
    tags=["IRVE Dynamique"],
)


@router.get("/status/", tags=["Status"])
async def list_statuses() -> List[Status]:
    """List last known point of charge statuses."""
    return []


@router.get("/status/{id_pdc_itinerance}", tags=["Status"])
async def read_status(
    id_pdc_itinerance: Annotated[
        str,
        Path(
            description=(
                "L'identifiant du point de recharge délivré selon les modalités "
                "définies à l'article 10 du décret n° 2017-26 du 12 janvier 2017."
            ),
        ),
    ],
) -> Status:
    """Read last known point of charge status."""
    raise NotImplementedError


@router.post("/status/", status_code=status.HTTP_201_CREATED, tags=["Status"])
async def create_status(status: Status) -> Status:
    """Create a status."""
    raise NotImplementedError
