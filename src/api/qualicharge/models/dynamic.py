"""QualiCharge dynamic odels."""

from enum import StrEnum
from typing import Optional

from pydantic import PositiveFloat
from pydantic.types import PastDatetime
from sqlmodel import Field, SQLModel


class EtatPDCEnum(StrEnum):
    """Status.etat_pdc field enum."""

    EN_SERVICE = "en_service"
    HORS_SERVICE = "hors_service"
    INCONNU = "inconnu"


class OccupationPDCEnum(StrEnum):
    """Status.occupation_pdc field enum."""

    LIBRE = "libre"
    OCCUPE = "occupe"
    RESERVE = "reserve"
    INCONNU = "inconnu"


class EtatPriseEnum(StrEnum):
    """Status.etat_prise_* fields enum."""

    FONCTIONNEL = "fonctionnel"
    HORS_SERVICE = "hors_service"
    INCONNU = "inconnu"


class StatusBase(SQLModel):
    """Base point of charge status."""

    etat_pdc: EtatPDCEnum
    occupation_pdc: OccupationPDCEnum
    horodatage: PastDatetime
    etat_prise_type_2: Optional[EtatPriseEnum]
    etat_prise_type_combo_ccs: Optional[EtatPriseEnum]
    etat_prise_type_chademo: Optional[EtatPriseEnum]
    etat_prise_type_ef: Optional[EtatPriseEnum]


class StatusCreate(StatusBase):
    """Point of charge status create."""

    id_pdc_itinerance: str = Field(
        regex="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$"
    )


class StatusRead(StatusCreate):
    """Point of charge status read."""


class SessionBase(SQLModel):
    """Base point of charge sessions."""

    start: PastDatetime
    end: PastDatetime
    energy: PositiveFloat


class SessionCreate(SessionBase):
    """Point of charge sessions create."""

    id_pdc_itinerance: str = Field(
        regex="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$"
    )
