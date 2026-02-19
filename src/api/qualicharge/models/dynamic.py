"""QualiCharge dynamic odels."""

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Annotated, Optional
from zoneinfo import ZoneInfo

from annotated_types import Ge, Le
from pydantic import AfterValidator, model_validator
from pydantic.types import AwareDatetime, PastDatetime
from sqlmodel import Field, SQLModel
from typing_extensions import Self

from ..conf import settings

AwarePastDatetime = Annotated[AwareDatetime, PastDatetime]


def is_aware(value: datetime):
    """Check if a datetime instance is aware or not."""
    return value.tzinfo is not None and value.tzinfo.utcoffset(value) is not None


def set_default_tz(value: datetime):
    """Set the default timezone to value."""
    return value.replace(tzinfo=ZoneInfo(settings.DEFAULT_TZ))


def not_older_than(value: datetime, max_age: timedelta):
    """Validator function to ensure a datetime is not older than a now - max_age."""
    now = datetime.now(tz=timezone.utc)
    if not is_aware(value):
        value = set_default_tz(value)
    if value < now - max_age:
        raise ValueError(f"{value} is older than {max_age}")
    return value


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
    """Base charge point status."""

    etat_pdc: EtatPDCEnum
    occupation_pdc: OccupationPDCEnum
    horodatage: PastDatetime
    etat_prise_type_2: Optional[EtatPriseEnum] = None
    etat_prise_type_combo_ccs: Optional[EtatPriseEnum] = None
    etat_prise_type_chademo: Optional[EtatPriseEnum] = None
    etat_prise_type_ef: Optional[EtatPriseEnum] = None


class StatusAPIBase(StatusBase):
    """Base charge point status for the API."""

    id_pdc_itinerance: str = Field(
        regex="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$",
        schema_extra={
            "examples": ["FR0NXEVSEXB9YG", "FRFASE3300405", "FR073012308585"]
        },
    )


class StatusCreate(StatusAPIBase):
    """Point of charge status create."""

    horodatage: Annotated[
        AwarePastDatetime,
        AfterValidator(
            lambda v: not_older_than(v, timedelta(seconds=settings.API_MAX_STATUS_AGE))
        ),
    ]


class StatusRead(StatusAPIBase):
    """Point of charge status read."""


class SessionBase(SQLModel):
    """Base point of charge sessions."""

    start: PastDatetime
    end: PastDatetime
    energy: Annotated[float, Ge(0.0), Le(1000.0)]

    @model_validator(mode="after")
    def check_session_dates(self) -> Self:
        """Check start/end dates consistency."""
        if self.start > self.end:
            raise ValueError("A session cannot start after it has ended.")
        return self


class SessionCreate(SessionBase):
    """Point of charge sessions create."""

    id_pdc_itinerance: str = Field(
        regex="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$",
        schema_extra={
            "examples": ["FR0NXEVSEXB9YG", "FRFASE3300405", "FR073012308585"]
        },
    )
    start: Annotated[
        AwarePastDatetime,
        AfterValidator(
            lambda v: not_older_than(v, timedelta(seconds=settings.API_MAX_SESSION_AGE))
        ),
    ]
    end: AwarePastDatetime
