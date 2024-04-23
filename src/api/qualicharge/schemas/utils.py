"""QualiCharge schemas utilities."""

import logging
from typing import Generator, List, NamedTuple, Optional, Set, Tuple, Type, cast

from sqlalchemy import func
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Session, SQLModel, select

from ..exceptions import (
    DatabaseQueryException,
    DuplicateEntriesSubmitted,
    IntegrityError,
    ObjectDoesNotExist,
)
from ..models.static import Statique
from .static import (
    Amenageur,
    Enseigne,
    Localisation,
    Operateur,
    PointDeCharge,
    Station,
)

logger = logging.getLogger(__name__)

DB_TO_STATIC_EXCLUDED_FIELDS = {"id", "created_at", "updated_at"}


def get_or_create(  # noqa: PLR0913
    session: Session,
    entry: SQLModel,
    fields: Optional[Set] = None,
    add: bool = True,
    commit: bool = True,
    refresh: bool = False,
) -> Tuple[bool, SQLModel]:
    """Get or create schema instance.

    Args:
        session: SQLModel session
        entry: SQLModel schema instance
        fields: entry fields used in database query to select target entry.
                Defaults to None (use all fields).
        add: should we add the schema instance to the session?
        commit: should we commit transation to database?
        refresh: should we refresh the schema instance from database?

    Returns:
        A (bool, entry) tuple. The boolean states on the entry creation.

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
        return False, db_entry

    # Handle new entry
    if add:
        session.add(entry)
    if commit:
        session.commit()
    if refresh:
        session.refresh(entry)
    return True, entry


def save_schema_from_statique(
    session: Session,
    schema_klass: Type[SQLModel],
    statique: Statique,
    fields: Optional[Set] = None,
) -> Tuple[bool, SQLModel]:
    """Save schema to database from Statique instance.

    Args:
        session: SQLModel session
        schema_klass: SQLModel schema class to save from Statique
        statique: input static model definition
        fields: entry fields used in database query to select target entry.
                Defaults to None (use all fields).

    Returns:
        A (bool, entry) tuple. The boolean states on the entry creation.

    Raises:
        DatabaseQueryException: Found multiple entries given input fields.
    """
    # Is this a new entry?
    entry = schema_klass(**statique.get_fields_for_schema(schema_klass))
    return get_or_create(
        session,
        entry,
        fields=fields,
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


def save_statique(session: Session, statique: Statique) -> Statique:
    """Save Statique instance to database."""
    # Core schemas
    _, pdc = save_schema_from_statique(
        session, PointDeCharge, statique, fields={"id_pdc_itinerance"}
    )
    _, station = save_schema_from_statique(
        session, Station, statique, fields={"id_station_itinerance"}
    )
    _, amenageur = save_schema_from_statique(session, Amenageur, statique)
    _, operateur = save_schema_from_statique(session, Operateur, statique)
    _, enseigne = save_schema_from_statique(session, Enseigne, statique)
    _, localisation = save_schema_from_statique(
        session,
        Localisation,
        statique,
        fields={
            "adresse_station",
        },
    )

    # Relationships
    pdc.station_id = station.id  # type: ignore[attr-defined]
    station.amenageur_id = amenageur.id  # type: ignore[attr-defined]
    station.operateur_id = operateur.id  # type: ignore[attr-defined]
    station.enseigne_id = enseigne.id  # type: ignore[attr-defined]
    station.localisation_id = localisation.id  # type: ignore[attr-defined]

    session.add(pdc)
    session.add(station)
    session.commit()
    session.refresh(pdc)

    return pdc_to_statique(cast(PointDeCharge, pdc))


def update_statique(
    session: Session, id_pdc_itinerance: str, update: Statique
) -> Statique:
    """Update given statique from its id_pdc_itinerance."""
    # Check that submitted id_pdc_itinerance corresponds to the update
    if id_pdc_itinerance != update.id_pdc_itinerance:
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

    return save_statique(session, update)


def save_statiques(
    session: Session, statiques: List[Statique]
) -> Generator[Statique, None, None]:
    """Save Statique instances to database in an efficient way."""
    # Look for duplicates (identical id_pdc_itinerance)
    submitted_pdcs = {s.id_pdc_itinerance for s in statiques}
    if len(submitted_pdcs) != len(statiques):
        raise DuplicateEntriesSubmitted("Found duplicated entries in submitted data")

    # Ignore already existing PDC
    db_pdcs = session.exec(
        select(PointDeCharge.id_pdc_itinerance).filter(
            cast(SAColumn, PointDeCharge.id_pdc_itinerance).in_(submitted_pdcs)
        )
    ).all()
    statiques = list(filter(lambda s: s.id_pdc_itinerance not in db_pdcs, statiques))
    if not len(statiques):
        return None

    # Entries to get or create per schema
    points_de_charge: List[PointDeCharge] = []
    stations: List[Station] = []
    amenageurs: List[Amenageur] = []
    operateurs: List[Operateur] = []
    enseignes: List[Enseigne] = []
    localisations: List[Localisation] = []

    class StatiqueSchemasEntryIndex(NamedTuple):
        """Statique entry decoupled as suite of schema indexes.

        We use this pivot representation to mimic foreign key relationships that
        ensure the uniqueness of related entities.
        """

        pdc: int
        station: int
        amenageur: int
        operateur: int
        enseigne: int
        localisation: int

    # Collect unique entries list per model and add references to those for each
    # Statique
    statiques_db_refs: List[StatiqueSchemasEntryIndex] = []
    for statique in statiques:
        pdc = PointDeCharge(**statique.get_fields_for_schema(PointDeCharge))
        station = Station(**statique.get_fields_for_schema(Station))
        amenageur = Amenageur(**statique.get_fields_for_schema(Amenageur))
        operateur = Operateur(**statique.get_fields_for_schema(Operateur))
        enseigne = Enseigne(**statique.get_fields_for_schema(Enseigne))
        localisation = Localisation(**statique.get_fields_for_schema(Localisation))

        indexes = []
        # FIXME
        # Looks like mypy does not recognize types for tuple of tuples to unpack,
        # ignored unrelevant typing errors.
        for entry, entries in (
            (pdc, points_de_charge),
            (station, stations),
            (amenageur, amenageurs),
            (operateur, operateurs),
            (enseigne, enseignes),
            (localisation, localisations),
        ):
            if entry not in entries:  # type: ignore[operator]
                entries.append(entry)  # type: ignore[attr-defined]
            indexes.append(entries.index(entry))  # type: ignore[attr-defined]
        statiques_db_refs.append(StatiqueSchemasEntryIndex(*indexes))

    # Create database entries for each schema
    #
    # FIXME
    # Looks like mypy does not recognize types for tuple of tuples to unpack,
    # ignored unrelevant typing errors.
    for entries, fields in (
        (points_de_charge, {"id_pdc_itinerance"}),
        (stations, {"id_station_itinerance"}),
        (amenageurs, None),
        (operateurs, None),
        (enseignes, None),
        (localisations, {"adresse_station"}),
    ):
        for idx, entry in enumerate(entries):  # type: ignore[arg-type]
            _, db_entry = get_or_create(
                session, entry, fields, add=False, commit=False, refresh=False
            )
            entries[idx] = db_entry  # type: ignore[index]
        session.add_all(entries)  # type: ignore[arg-type]

    # Handle relationships
    for (
        pdc_idx,
        station_idx,
        amenageur_idx,
        operateur_idx,
        enseigne_idx,
        localisation_idx,
    ) in statiques_db_refs:
        points_de_charge[pdc_idx].station_id = stations[station_idx].id  # type: ignore[attr-defined]
        stations[station_idx].amenageur_id = amenageurs[amenageur_idx].id  # type: ignore[attr-defined]
        stations[station_idx].operateur_id = operateurs[operateur_idx].id  # type: ignore[attr-defined]
        stations[station_idx].enseigne_id = enseignes[enseigne_idx].id  # type: ignore[attr-defined]
        stations[station_idx].localisation_id = localisations[localisation_idx].id  # type: ignore[attr-defined]

    # Commit transaction
    session.commit()

    for pdc in points_de_charge:
        session.refresh(pdc)
        yield pdc_to_statique(pdc)


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
    session: Session, offset: int = 0, limit: int = 50
) -> Generator[Statique, None, None]:
    """List Statique entries."""
    for pdc in session.exec(
        select(PointDeCharge)
        .order_by(PointDeCharge.id_pdc_itinerance)
        .offset(offset)
        .limit(limit)
    ).all():
        yield pdc_to_statique(pdc)
