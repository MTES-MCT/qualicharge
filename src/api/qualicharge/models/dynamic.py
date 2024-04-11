"""QualiCharge dynamic odels."""

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field
from pydantic.types import PastDatetime
from typing_extensions import Annotated


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


class Status(BaseModel):
    """IRVE dynamic model: point of charge status."""

    id_pdc_itinerance: Annotated[str, Field(pattern="^[A-Z]{2}[A-Z0-9]{4,33}$")]
    etat_pdc: EtatPDCEnum
    occupation_pdc: OccupationPDCEnum
    horodatage: PastDatetime
    etat_prise_type_2: Optional[EtatPriseEnum]
    etat_prise_type_combo_ccs: Optional[EtatPriseEnum]
    etat_prise_type_chademo: Optional[EtatPriseEnum]
    etat_prise_type_ef: Optional[EtatPriseEnum]


class Session(BaseModel):
    """IRVE dynamic model: point of charge sessions."""

    id_pdc_itinerance: Annotated[str, Field(pattern="^[A-Z]{2}[A-Z0-9]{4,33}$")]
    start: PastDatetime
    end: PastDatetime
    energy: float
