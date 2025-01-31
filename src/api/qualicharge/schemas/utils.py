"""QualiCharge schemas utilities."""

import logging
from enum import IntEnum
from io import BytesIO
from typing import Generator, List, Optional, Set, Tuple, Type, cast

import pandas as pd
from sqlalchemy import func
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, SQLModel, select

from qualicharge.auth.schemas import User
from qualicharge.schemas import BaseAuditableSQLModel

from ..exceptions import (
    DatabaseQueryException,
    IntegrityError,
    ObjectDoesNotExist,
)
from ..models.static import Statique
from ..schemas.sql import StatiqueImporter
from .core import (
    Amenageur,
    Enseigne,
    Localisation,
    Operateur,
    OperationalUnit,
    PointDeCharge,
    Station,
)

logger = logging.getLogger(__name__)

DB_TO_STATIC_EXCLUDED_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "created_by_id",
    "updated_by_id",
}


class EntryStatus(IntEnum):
    """Describe entry status."""

    EXISTS = 0
    CREATED = 1
    UPDATED = 2


def get_or_create(
    session: Session,
    entry: SQLModel,
    fields: Optional[Set] = None,
    add: bool = True,
    update: bool = False,
) -> Tuple[EntryStatus, SQLModel]:
    """Get or create schema instance.

    Args:
        session: SQLModel session
        entry: SQLModel schema instance
        fields: entry fields used in database query to select target entry.
                Defaults to None (use all fields).
        add: should we add the schema instance to the session?
        update: should we update existing instance if required?

    Returns:
        A (EntryStatus, entry) tuple. The status refers on the entry creation/update.

    Raises:
        DatabaseQueryException: Found multiple entries given input fields.
    """
    # Try to get entry from selected fields
    statement = select(entry.__class__).filter_by(
        **entry.model_dump(include=fields, exclude=DB_TO_STATIC_EXCLUDED_FIELDS)
    )
    try:
        db_entry = session.exec(statement).one_or_none()
    except MultipleResultsFound as err:
        raise DatabaseQueryException(
            f"Multiple results found for input fields {fields}"
        ) from err

    if db_entry is not None:
        logger.debug(f"Found database entry with id: {db_entry.id}")  # type: ignore[attr-defined]
        if not update:
            return EntryStatus.EXISTS, db_entry

        # Update database entry
        for key, value in entry.model_dump(
            exclude=set(DB_TO_STATIC_EXCLUDED_FIELDS) - {"updated_by_id"}
        ).items():
            setattr(db_entry, key, value)
        session.add(db_entry)

        return EntryStatus.UPDATED, db_entry

    # Add new entry
    if add:
        session.add(entry)

    return EntryStatus.CREATED, entry


def save_schema_from_statique(  # noqa: PLR0913
    session: Session,
    schema_klass: Type[SQLModel],
    statique: Statique,
    fields: Optional[Set] = None,
    update: bool = False,
    author: Optional[User] = None,
) -> Tuple[EntryStatus, SQLModel]:
    """Save schema to database from Statique instance.

    Args:
        session: SQLModel session
        schema_klass: SQLModel schema class to save from Statique
        statique: input static model definition
        fields: entry fields used in database query to select target entry.
                Defaults to None (use all fields).
        update: should we update existing instance if required?
        author: the user that creates/updates the schema entry

    Returns:
        A (EntryStatus, entry) tuple. The status refers on the entry creation/update.

    Raises:
        DatabaseQueryException: Found multiple entries given input fields.
    """
    # Is this a new entry?
    entry = schema_klass(**statique.get_fields_for_schema(schema_klass))

    # Add author for auditability
    if issubclass(schema_klass, BaseAuditableSQLModel):
        if update:
            entry.updated_by_id = author.id if author else None
        else:
            entry.created_by_id = author.id if author else None

    return get_or_create(
        session,
        entry,
        fields=fields,
        update=update,
    )


def pdc_to_statique(pdc: PointDeCharge) -> Statique:
    """Generate a Statique model instance from a PointDeCharge instance."""
    return Statique(
        **pdc.model_dump(exclude=DB_TO_STATIC_EXCLUDED_FIELDS),
        **pdc.station.model_dump(exclude=DB_TO_STATIC_EXCLUDED_FIELDS),
        **pdc.station.operateur.model_dump(exclude=DB_TO_STATIC_EXCLUDED_FIELDS),
        **pdc.station.amenageur.model_dump(exclude=DB_TO_STATIC_EXCLUDED_FIELDS),
        **pdc.station.enseigne.model_dump(exclude=DB_TO_STATIC_EXCLUDED_FIELDS),
        **pdc.station.localisation.model_dump(exclude=DB_TO_STATIC_EXCLUDED_FIELDS),
    )


def save_statique(
    session: Session,
    statique: Statique,
    update: bool = False,
    author: Optional[User] = None,
) -> Statique:
    """Save Statique instance to database."""
    # Core schemas
    _, pdc = save_schema_from_statique(
        session,
        PointDeCharge,
        statique,
        fields={"id_pdc_itinerance"},
        update=update,
        author=author,
    )
    _, station = save_schema_from_statique(
        session,
        Station,
        statique,
        fields={"id_station_itinerance"},
        update=update,
        author=author,
    )
    _, amenageur = save_schema_from_statique(
        session, Amenageur, statique, update=update, author=author
    )
    _, operateur = save_schema_from_statique(
        session, Operateur, statique, update=update, author=author
    )
    _, enseigne = save_schema_from_statique(
        session, Enseigne, statique, update=update, author=author
    )
    _, localisation = save_schema_from_statique(
        session,
        Localisation,
        statique,
        fields={
            "adresse_station",
        },
        update=update,
        author=author,
    )

    # Relationships
    pdc.station_id = station.id  # type: ignore[attr-defined]
    station.amenageur_id = amenageur.id  # type: ignore[attr-defined]
    station.operateur_id = operateur.id  # type: ignore[attr-defined]
    station.enseigne_id = enseigne.id  # type: ignore[attr-defined]
    station.localisation_id = localisation.id  # type: ignore[attr-defined]

    session.refresh(amenageur)
    session.refresh(operateur)
    session.refresh(enseigne)
    session.refresh(localisation)
    session.refresh(station)
    session.refresh(pdc)

    return pdc_to_statique(cast(PointDeCharge, pdc))


def update_statique(
    session: Session,
    id_pdc_itinerance: str,
    to_update: Statique,
    author: Optional[User] = None,
) -> Statique:
    """Update given statique from its id_pdc_itinerance."""
    # Check that submitted id_pdc_itinerance corresponds to the update
    if id_pdc_itinerance != to_update.id_pdc_itinerance:
        raise IntegrityError(
            "Cannot update statique with a different id_pdc_itinerance"
        )

    # Check that the statique to update exists
    if (
        session.exec(
            select(func.count(cast(SAColumn, PointDeCharge.id))).where(
                PointDeCharge.id_pdc_itinerance == id_pdc_itinerance
            )
        ).one()
        != 1
    ):
        raise ObjectDoesNotExist("Statique with id_pdc_itinerance does not exist")

    return save_statique(session, to_update, update=True, author=author)


def save_statiques(
    db_session: Session, statiques: List[Statique], author: Optional[User] = None
):
    """Save input statiques to database."""
    df = pd.read_json(
        BytesIO(
            bytes(f"{'\n'.join([s.model_dump_json() for s in statiques])}", "utf-8")
        ),
        lines=True,
        orient="records",
        engine="pyarrow",
        dtype_backend="pyarrow",
    )
    importer = StatiqueImporter(df, db_session.connection(), author=author)
    importer.save()


def build_statique(session: Session, id_pdc_itinerance: str) -> Statique:
    """Build Statique instance from database."""
    pdc = session.exec(
        select(PointDeCharge).where(
            PointDeCharge.id_pdc_itinerance == id_pdc_itinerance
        )
    ).one_or_none()

    if pdc is None:
        raise ObjectDoesNotExist("Statique with id_pdc_itinerance does not exist")

    return pdc_to_statique(pdc)


# TODO add filters support
def list_statique(
    session: Session,
    offset: int = 0,
    limit: int = 50,
    operational_units: Optional[List[OperationalUnit]] = None,
) -> Generator[Statique, None, None]:
    """List Statique entries."""
    statement = select(PointDeCharge)
    if operational_units:
        statement = (
            statement.join_from(
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
                    ou.id for ou in operational_units
                )
            )
        )
    statement = (
        statement.order_by(PointDeCharge.id_pdc_itinerance).offset(offset).limit(limit)
    )
    for pdc in session.exec(statement).all():
        yield pdc_to_statique(pdc)


def is_pdc_allowed_for_user(id_pdc_itinerance: str, user: User) -> bool:
    """Check if a user can create/read/update a PDC given its identifier."""
    if user.is_superuser:
        return True
    if id_pdc_itinerance[:5] in [ou.code for ou in user.operational_units]:
        return True
    return False


def are_pdcs_allowed_for_user(ids_pdc_itinerance: set | list, user) -> bool:
    """Check of a user can create/read/update a list of PDCs given their identifiers."""
    if user.is_superuser:
        return True
    operational_unit_codes: set = {id_[:5] for id_ in ids_pdc_itinerance}
    user_operational_unit_codes: set = {ou.code for ou in user.operational_units}
    return operational_unit_codes.issubset(user_operational_unit_codes)
