"""QualiCharge API v1 dynamique router."""

import logging
from typing import Annotated, List

from fastapi import APIRouter, Path, status

from qualicharge.models.dynamic import (
    SessionCreate,
    StatusCreate,
    StatusRead,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dynamique",
    tags=["IRVE Dynamique"],
)


@router.get("/status/", tags=["Status"])
async def list_statuses() -> List[StatusRead]:
    """List last known point of charge statuses."""
    raise NotImplementedError


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
) -> StatusRead:
    """Read last known point of charge status."""
    raise NotImplementedError


@router.get("/status/{id_pdc_itinerance}/history", tags=["Status"])
async def read_status_history(
    id_pdc_itinerance: Annotated[
        str,
        Path(
            description=(
                "L'identifiant du point de recharge délivré selon les modalités "
                "définies à l'article 10 du décret n° 2017-26 du 12 janvier 2017."
            ),
        ),
    ],
) -> List[StatusRead]:
    """Read point of charge status history."""
    raise NotImplementedError


@router.post("/status/", status_code=status.HTTP_201_CREATED, tags=["Status"])
async def create_status(status: StatusCreate) -> None:
    """Create a status."""
    raise NotImplementedError


@router.post("/status/bulk", status_code=status.HTTP_201_CREATED, tags=["Status"])
async def create_status_bulk(statuses: List[StatusCreate]) -> None:
    """Create a statuses batch."""
    raise NotImplementedError


@router.post("/session/", status_code=status.HTTP_201_CREATED, tags=["Session"])
async def create_session(session: SessionCreate) -> None:
    """Create a session."""
    raise NotImplementedError


@router.post("/session/bulk", status_code=status.HTTP_201_CREATED, tags=["Session"])
async def create_session_bulk(sessions: List[SessionCreate]) -> None:
    """Create a sessions batch."""
    raise NotImplementedError
