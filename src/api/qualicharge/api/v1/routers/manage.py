"""QualiCharge API v1 manage router."""

import logging
from typing import Annotated, List, cast

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Security,
    status,
)
from pydantic import (
    BaseModel,
    Field,
    PastDatetime,
)
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, select

from qualicharge.api.utils import GzipRoute
from qualicharge.auth.oidc import get_user
from qualicharge.auth.schemas import ScopesEnum, User
from qualicharge.db import get_session
from qualicharge.schemas.core import Station

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/manage",
    tags=["management"],
    route_class=GzipRoute,
)


class DashboardStation(BaseModel):
    """Station model for the Dashboard app."""

    id_station_itinerance: Annotated[
        str, Field(pattern="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$")
    ]
    nom_station: str
    num_pdl: Annotated[str, Field(max_length=64)]
    updated_at: PastDatetime


@router.get("/station/siren/{siren}")
async def stations_by_siren(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.MANAGE_READ.value])],
    siren: Annotated[
        str,
        Path(
            description="Numéro SIREN de l'entreprise en charge de la station",
            pattern=r"^\d{9}$",
        ),
    ],
    after: PastDatetime | None = None,
    session: Session = Depends(get_session),
) -> List[DashboardStation]:
    """List stations for a given company identified by its SIREN."""
    statement = select(Station).where(
        (cast(SAColumn, Station.amenageur).has(siren_amenageur=siren))
        & (Station.num_pdl != None)  # noqa: E711
        & (Station.num_pdl != "")
    )
    if after is not None:
        statement = statement.where(Station.updated_at >= after)

    stations = session.exec(statement).all()
    if not len(stations):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=("No station corresponds to your request"),
        )

    return [
        DashboardStation(
            id_station_itinerance=s.id_station_itinerance,
            nom_station=s.nom_station,
            num_pdl=s.num_pdl,
            updated_at=s.updated_at,
        )
        for s in stations
    ]
