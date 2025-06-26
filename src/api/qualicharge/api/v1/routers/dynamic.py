"""QualiCharge API v1 dynamique router."""

import logging
from threading import Lock
from typing import Annotated, List, cast
from uuid import UUID, uuid4

from annotated_types import Len
from cachetools import LRUCache, cached
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    Security,
)
from fastapi import status as fa_status
from pydantic import UUID4, BaseModel, PastDatetime, StringConstraints
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, join, select

from qualicharge.api.utils import GzipRoute
from qualicharge.auth.oidc import get_user
from qualicharge.auth.schemas import ScopesEnum, User
from qualicharge.conf import settings
from qualicharge.db import get_session
from qualicharge.exceptions import PermissionDenied
from qualicharge.models.dynamic import (
    SessionCreate,
    StatusCreate,
    StatusRead,
)
from qualicharge.schemas.core import LatestStatus, PointDeCharge, Station, Status
from qualicharge.schemas.core import Session as QCSession
from qualicharge.schemas.utils import are_pdcs_allowed_for_user, is_pdc_allowed_for_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dynamique",
    tags=["IRVE Dynamique"],
    route_class=GzipRoute,
)

BulkStatusCreateList = Annotated[
    List[StatusCreate], Len(1, settings.API_STATUS_BULK_CREATE_MAX_SIZE)
]
BulkSessionCreateList = Annotated[
    List[SessionCreate], Len(1, settings.API_SESSION_BULK_CREATE_MAX_SIZE)
]
IdItinerance = Annotated[
    str,
    StringConstraints(pattern="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$"),
]


class DynamiqueItemCreatedResponse(BaseModel):
    """API response model used when a dynamic item is created."""

    id: UUID4


class DynamiqueItemsCreatedResponse(BaseModel):
    """API response model used when dynamic items are created."""

    size: int
    items: List[UUID4]


@cached(
    LRUCache(
        maxsize=settings.API_GET_PDC_ID_CACHE_MAXSIZE,
    ),
    lock=Lock(),
    key=lambda id_pdc_itinerance, session: id_pdc_itinerance,
    info=settings.API_GET_PDC_ID_CACHE_INFO,
)
def get_pdc_id(id_pdc_itinerance: str, session: Session) -> UUID:
    """Get PointDeCharge.id from an `id_pdc_itinerance`."""
    pdc_id = session.exec(
        select(PointDeCharge.id).where(
            PointDeCharge.id_pdc_itinerance == id_pdc_itinerance
        )
    ).one_or_none()

    if pdc_id is not None:
        return pdc_id

    raise HTTPException(
        status_code=fa_status.HTTP_404_NOT_FOUND,
        detail="Point of charge does not exist",
    )


@router.get("/status/", tags=["Status"])
async def list_statuses(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.DYNAMIC_READ.value])],
    from_: Annotated[
        PastDatetime | None,
        Query(
            alias="from",
            title="Date/time from",
            description="The datetime from when we want statuses to be collected",
        ),
    ] = None,
    pdc: Annotated[
        List[IdItinerance] | None,
        Query(
            title="Point de charge",
            description=(
                "Filter status by `id_pdc_itinerance` (can be provided multiple times)"
            ),
        ),
    ] = None,
    station: Annotated[
        List[IdItinerance] | None,
        Query(
            title="Station",
            description=(
                "Filter status by `id_station_itinerance` "
                "(can be provided multiple times)"
            ),
        ),
    ] = None,
    session: Session = Depends(get_session),
) -> List[StatusRead]:
    """List last known points of charge status."""
    pdc_ids_filter = set()

    # Filter by station
    if station:
        pdc_ids_filter = set(
            session.exec(
                select(PointDeCharge.id_pdc_itinerance)
                .select_from(
                    join(
                        PointDeCharge,
                        Station,
                        cast(SAColumn, PointDeCharge.station_id)
                        == cast(SAColumn, Station.id),
                    )
                )
                .filter(cast(SAColumn, Station.id_station_itinerance).in_(station))
            ).all()
        )

    # Filter by point of charge
    if pdc:
        pdc_ids_filter = pdc_ids_filter | set(pdc)

    # Get latest status per point of charge
    db_statuses_stmt = select(LatestStatus)

    if from_:
        db_statuses_stmt = db_statuses_stmt.where(LatestStatus.horodatage >= from_)

    if len(pdc_ids_filter):
        db_statuses_stmt = db_statuses_stmt.filter(
            cast(SAColumn, LatestStatus.id_pdc_itinerance).in_(pdc_ids_filter)
        )

    if not user.is_superuser:
        db_statuses_stmt = (
            db_statuses_stmt.join_from(
                LatestStatus,
                PointDeCharge,
                LatestStatus.id_pdc_itinerance == PointDeCharge.id_pdc_itinerance,  # type: ignore[arg-type]
            )
            .join_from(PointDeCharge, Station, PointDeCharge.station_id == Station.id)  # type: ignore[arg-type]
            .filter(
                cast(SAColumn, Station.operational_unit_id).in_(
                    ou.id for ou in user.operational_units
                )
            )
        )

    db_statuses = session.exec(db_statuses_stmt).all()

    return [
        StatusRead(
            **s.model_dump(
                exclude={
                    "id",
                    "point_de_charge_id",
                }
            )
        )
        for s in db_statuses
        if s is not None
    ]


@router.get("/status/{id_pdc_itinerance}", tags=["Status"])
async def read_status(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.DYNAMIC_READ.value])],
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
) -> StatusRead:
    """Read last known point of charge status."""
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You cannot read the status of this point of charge")

    # Ensure charge point exists
    get_pdc_id(id_pdc_itinerance, session)

    db_status = session.exec(
        select(LatestStatus).where(LatestStatus.id_pdc_itinerance == id_pdc_itinerance)
    ).one_or_none()
    if db_status is None:
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail="Selected point of charge does not have status record yet",
        )

    return StatusRead(
        **db_status.model_dump(
            exclude={
                "id",
                "point_de_charge_id",
            }
        )
    )


@router.get("/status/{id_pdc_itinerance}/history", tags=["Status"])
async def read_status_history(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.DYNAMIC_READ.value])],
    id_pdc_itinerance: Annotated[
        str,
        Path(
            description=(
                "L'identifiant du point de recharge délivré selon les modalités "
                "définies à l'article 10 du décret n° 2017-26 du 12 janvier 2017."
            ),
        ),
    ],
    from_: Annotated[
        PastDatetime | None,
        Query(
            alias="from",
            title="Date/time from",
            description="The datetime from when we want statuses to be collected",
        ),
    ] = None,
    session: Session = Depends(get_session),
) -> List[StatusRead]:
    """Read point of charge status history."""
    if not is_pdc_allowed_for_user(id_pdc_itinerance, user):
        raise PermissionDenied("You cannot read statuses of this point of charge")

    pdc_id = get_pdc_id(id_pdc_itinerance, session)

    # Get latest statuses
    db_statuses_stmt = select(Status).where(Status.point_de_charge_id == pdc_id)

    if from_:
        db_statuses_stmt = db_statuses_stmt.where(Status.horodatage >= from_)

    db_statuses = session.exec(
        db_statuses_stmt.order_by(cast(SAColumn, Status.horodatage))
    ).all()

    if not len(db_statuses):
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail="Selected point of charge does not have status record yet",
        )
    return [
        StatusRead(
            **s.model_dump(
                exclude={
                    "id",
                    "point_de_charge_id",
                }
            )
        )
        for s in db_statuses
    ]


def _create_status(
    session: Session, status: StatusCreate, status_id: UUID, pdc_id: UUID
) -> None:
    """Background task that creates a POC status.

    Nota bene: we expect the last-received status to be the most recent one.
    This assumption may be false, but it's a good compromise between performance
    and consistency. Adding this check would be too greedy.
    """
    db_status = Status(id=status_id, **status.model_dump(exclude={"id_pdc_itinerance"}))
    db_status.point_de_charge_id = pdc_id
    session.add(db_status)

    # Upsert latest status
    stmt = insert(LatestStatus).values(**status.model_dump())
    updates_on_conflict = status.model_dump(exclude={"id_pdc_itinerance"})
    updates_on_conflict.update({"updated_at": stmt.excluded.updated_at})
    stmt = stmt.on_conflict_do_update(
        constraint="lateststatus_pkey",
        set_=updates_on_conflict,
    )
    session.execute(stmt)

    # Commit transaction
    session.commit()


@router.post("/status/", status_code=fa_status.HTTP_201_CREATED, tags=["Status"])
async def create_status(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.DYNAMIC_CREATE.value])],
    background_tasks: BackgroundTasks,
    status: StatusCreate,
    session: Session = Depends(get_session),
) -> DynamiqueItemCreatedResponse:
    """Create a status."""
    if not is_pdc_allowed_for_user(status.id_pdc_itinerance, user):
        raise PermissionDenied("You cannot create statuses for this point of charge")

    pdc_id = get_pdc_id(status.id_pdc_itinerance, session)
    status_id = uuid4()
    background_tasks.add_task(_create_status, session, status, status_id, pdc_id)

    return DynamiqueItemCreatedResponse(id=status_id)


def _create_status_bulk(
    session: Session,
    statuses: List[StatusCreate],
    status_ids: List[UUID],
    db_pdcs: dict,
) -> None:
    """Background task that creates POCs status batch."""
    db_statuses = []
    db_latest_statuses: dict[str, dict] = {}
    for status, status_id in zip(statuses, status_ids, strict=True):
        db_status = Status(
            id=status_id, **status.model_dump(exclude={"id_pdc_itinerance"})
        )
        db_status.point_de_charge_id = db_pdcs[status.id_pdc_itinerance]
        db_statuses.append(db_status)

        # If we have multiple statuses for a PDC in this batch, only keep the latest one
        if (
            status.id_pdc_itinerance in db_latest_statuses
            and db_latest_statuses[status.id_pdc_itinerance]["horodatage"]
            > status.horodatage
        ):
            continue
        db_latest_statuses[status.id_pdc_itinerance] = status.model_dump()
    session.add_all(db_statuses)

    # Upsert latest statuses
    stmt = insert(LatestStatus).values(list(db_latest_statuses.values()))
    updates_on_conflict = {
        f: stmt.excluded.get(f)
        for f in StatusCreate.model_fields.keys()
        if f != "id_pdc_itinerance"
    }
    updates_on_conflict.update({"updated_at": stmt.excluded.updated_at})
    stmt = stmt.on_conflict_do_update(
        constraint="lateststatus_pkey",
        set_=updates_on_conflict,
    )
    session.execute(stmt)

    # Commit transaction
    session.commit()


@router.post("/status/bulk", status_code=fa_status.HTTP_201_CREATED, tags=["Status"])
async def create_status_bulk(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.DYNAMIC_CREATE.value])],
    background_tasks: BackgroundTasks,
    statuses: BulkStatusCreateList,
    session: Session = Depends(get_session),
) -> DynamiqueItemsCreatedResponse:
    """Create a statuses batch.

    If an error occurs during batch importation, the database session is rolled
    back, hence none of the submitted statuses is saved.
    """
    ids_pdc_itinerance = {s.id_pdc_itinerance for s in statuses}
    if not are_pdcs_allowed_for_user(ids_pdc_itinerance, user):
        raise PermissionDenied(
            "You cannot submit data for an organization you are not assigned to"
        )

    # Create a dict with keys as id_pdc_itinerance and values as PDC id
    # for existing PDCs
    db_pdcs = dict(
        session.exec(
            select(PointDeCharge.id_pdc_itinerance, PointDeCharge.id).filter(
                cast(SAColumn, PointDeCharge.id_pdc_itinerance).in_(ids_pdc_itinerance)
            )
        ).all()
    )

    if len(db_pdcs) != len(ids_pdc_itinerance):
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail=(
                "Undeclared attached point(s) of charge, "
                "you should create them all first"
            ),
        )

    status_ids = [uuid4() for _ in statuses]
    background_tasks.add_task(
        _create_status_bulk, session, statuses, status_ids, db_pdcs
    )

    return DynamiqueItemsCreatedResponse(
        size=len(status_ids),
        items=status_ids,
    )


def _create_session(
    db_session: Session,
    session: SessionCreate,
    session_id: UUID,
    pdc_id: UUID,
    user_id: UUID,
) -> None:
    """Background task that creates a POC session."""
    qc_session = QCSession(
        id=session_id,
        **session.model_dump(exclude={"id_pdc_itinerance"}),
        created_by_id=user_id,
    )
    # Store session id so that we do not need to perform another request
    qc_session.point_de_charge_id = pdc_id
    db_session.add(qc_session)
    db_session.commit()


@router.post("/session/", status_code=fa_status.HTTP_201_CREATED, tags=["Session"])
async def create_session(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.DYNAMIC_CREATE.value])],
    background_tasks: BackgroundTasks,
    session: SessionCreate,
    db_session: Session = Depends(get_session),
) -> DynamiqueItemCreatedResponse:
    """Create a session."""
    if not is_pdc_allowed_for_user(session.id_pdc_itinerance, user):
        raise PermissionDenied("You cannot create sessions for this point of charge")

    # ⚠️ Please pay attention to the semantic:
    #
    # - `db_session` / `Session` refers to the database session, while,
    # - `session` / `QCSession` / `SessionCreate` refers to qualicharge charging session
    pdc_id = get_pdc_id(session.id_pdc_itinerance, db_session)

    qc_session_id = uuid4()
    background_tasks.add_task(
        _create_session, db_session, session, qc_session_id, pdc_id, user.id
    )

    return DynamiqueItemCreatedResponse(id=qc_session_id)


def _create_session_bulk(
    db_session: Session,
    sessions: List[SessionCreate],
    session_ids: List[UUID],
    db_pdcs: dict,
    user_id: UUID,
):
    """Background task that creates POCs session batch."""
    qc_sessions = []
    for session, session_id in zip(sessions, session_ids, strict=True):
        qc_session = QCSession(
            id=session_id,
            **session.model_dump(exclude={"id_pdc_itinerance"}),
            created_by_id=user_id,
        )
        qc_session.point_de_charge_id = db_pdcs[session.id_pdc_itinerance]
        qc_sessions.append(qc_session)
    db_session.add_all(qc_sessions)
    db_session.commit()


@router.post("/session/bulk", status_code=fa_status.HTTP_201_CREATED, tags=["Session"])
async def create_session_bulk(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.DYNAMIC_CREATE.value])],
    background_tasks: BackgroundTasks,
    sessions: BulkSessionCreateList,
    db_session: Session = Depends(get_session),
) -> DynamiqueItemsCreatedResponse:
    """Create a sessions batch.

    If an error occurs during batch importation, the database session is rolled
    back, hence none of the submitted sessions is saved.
    """
    ids_pdc_itinerance = {s.id_pdc_itinerance for s in sessions}
    if not are_pdcs_allowed_for_user(ids_pdc_itinerance, user):
        raise PermissionDenied(
            "You cannot submit data for an organization you are not assigned to"
        )

    # Create a dict with keys as id_pdc_itinerance and values as PDC id
    # for existing PDCs
    db_pdcs = dict(
        db_session.exec(
            select(PointDeCharge.id_pdc_itinerance, PointDeCharge.id).filter(
                cast(SAColumn, PointDeCharge.id_pdc_itinerance).in_(ids_pdc_itinerance)
            )
        ).all()
    )

    if len(db_pdcs) != len(ids_pdc_itinerance):
        raise HTTPException(
            status_code=fa_status.HTTP_404_NOT_FOUND,
            detail=(
                "Undeclared attached point(s) of charge, "
                "you should create them all first"
            ),
        )

    qc_session_ids = [uuid4() for _ in sessions]
    background_tasks.add_task(
        _create_session_bulk, db_session, sessions, qc_session_ids, db_pdcs, user.id
    )

    return DynamiqueItemsCreatedResponse(
        size=len(qc_session_ids),
        items=qc_session_ids,
    )


@router.get("/session/check", status_code=fa_status.HTTP_200_OK, tags=["Session"])
async def check_session(
    user: Annotated[User, Security(get_user, scopes=[ScopesEnum.DYNAMIC_READ.value])],
    session_id: UUID,
    db_session: Session = Depends(get_session),
) -> None:
    """Check if a session exists."""
    # ⚠️ Please pay attention to the semantic:
    #
    # - `db_session` / `Session` refers to the database session, while,
    # - `session` / `QCSession` / `SessionCreate` refers to qualicharge charging session
    stmt = select(func.count(cast(SAColumn, QCSession.id))).where(
        QCSession.id == session_id
    )
    counter = db_session.exec(stmt).one()
    if counter == 0:
        raise HTTPException(status_code=fa_status.HTTP_404_NOT_FOUND)
