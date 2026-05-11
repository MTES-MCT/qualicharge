"""QualiCharge tariff models."""

from datetime import date, datetime, time
from enum import StrEnum
from typing import Annotated, List, Optional, Union

from annotated_types import Ge
from pydantic import BaseModel, Field, StringConstraints, model_validator
from pydantic.types import AwareDatetime
from sqlmodel import SQLModel
from typing_extensions import Self

# https://github.com/loco-philippe/IRVE/blob/main/OCPI/source/schema.json


class PriceComponentTypeEnum(StrEnum):
    """Tariff price component dimensions."""

    ENERGY = "ENERGY"
    FLAT = "FLAT"
    PARKING_TIME = "PARKING_TIME"
    TIME = "TIME"
    CONGESTION_TIME = "CONGESTION_TIME"


class ReservationRestrictionEnum(StrEnum):
    """OCPI reservation restriction."""

    RESERVATION = "RESERVATION"
    RESERVATION_EXPIRES = "RESERVATION_EXPIRES"


class DayOfWeekEnum(StrEnum):
    """OCPI days of week."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class TaxIncludedEnum(StrEnum):
    """Whether tariff prices include taxes."""

    YES = "YES"
    NO = "NO"
    NA = "N/A"


class TariffAltText(BaseModel):
    """Localized tariff display text."""

    language: str
    text: str


class DisplayPrice(BaseModel):
    """OCPI 2.3 display price."""

    before_taxes: float
    after_taxes: Optional[float] = None


class Price(BaseModel):
    """OCPI 2.2 price with VAT split."""

    excl_vat: float
    incl_vat: Optional[float] = None


class PriceComponent(BaseModel):
    """A tariff price component."""

    type: PriceComponentTypeEnum
    price: Annotated[float, Ge(0.0)]
    vat: Optional[float] = None
    step_size: Optional[Annotated[int, Ge(1)]] = None


class TariffRestrictions(BaseModel):
    """Restrictions that control when a tariff element applies."""

    start_time: Optional[time] = None
    end_time: Optional[time] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_kwh: Optional[Annotated[float, Ge(0.0)]] = None
    max_kwh: Optional[Annotated[float, Ge(0.0)]] = None
    min_current: Optional[Annotated[float, Ge(0.0)]] = None
    max_current: Optional[Annotated[float, Ge(0.0)]] = None
    min_power: Optional[Annotated[float, Ge(0.0)]] = None
    max_power: Optional[Annotated[float, Ge(0.0)]] = None
    min_duration: Optional[Annotated[int, Ge(0)]] = None
    max_duration: Optional[Annotated[int, Ge(0)]] = None
    day_of_week: Optional[List[DayOfWeekEnum]] = None
    reservation: Optional[ReservationRestrictionEnum] = None
    min_vehicle_soc: Optional[Annotated[int, Ge(0)]] = None
    min_congestion_threshold: Optional[Annotated[int, Ge(0)]] = None


class TariffElement(BaseModel):
    """A tariff element, composed of prices and optional restrictions."""

    price_components: List[PriceComponent] = Field(min_length=1)
    restrictions: Optional[TariffRestrictions] = None


class TariffObject(BaseModel):
    """Internal tariff object compatible with a subset of OCPI."""

    country_code: Optional[
        Annotated[str, StringConstraints(min_length=2, max_length=2)]
    ] = None
    party_id: Optional[
        Annotated[str, StringConstraints(min_length=3, max_length=3)]
    ] = None
    tariff_id: str = Field(alias="id", max_length=36)
    currency: Optional[
        Annotated[str, StringConstraints(min_length=3, max_length=3)]
    ] = None
    elements: List[TariffElement] = Field(min_length=1)
    tariff_alt_text: Optional[List[TariffAltText]] = None
    start_date_time: Optional[AwareDatetime] = None
    end_date_time: Optional[AwareDatetime] = None
    last_updated: AwareDatetime
    tax_included: Optional[TaxIncludedEnum] = None
    min_price: Optional[Union[Annotated[float, Ge(0.0)], DisplayPrice]] = None
    max_price: Optional[Union[Price, DisplayPrice]] = None

    @model_validator(mode="after")
    def check_application_dates(self) -> Self:
        """Ensure tariff start/end dates are consistent."""
        if (
            self.start_date_time is not None
            and self.end_date_time is not None
            and self.start_date_time > self.end_date_time
        ):
            raise ValueError("A tariff cannot start after it has ended.")
        return self


class TariffCreate(SQLModel):
    """Tariff creation payload."""

    tariff: TariffObject = Field(alias="raw")
    id_pdc_itinerance: List[str] = Field(default_factory=list)


class TariffRead(SQLModel):
    """Tariff read payload."""

    id: str
    original_id: str
    original_last_updated: Optional[datetime]
    raw: TariffObject
    start: Optional[datetime]
    end: Optional[datetime]
    id_pdc_itinerance: List[str] = Field(default_factory=list)


class PointDeChargeTariffCreate(SQLModel):
    """Associate a tariff with charge points."""

    original_id: str
    original_last_updated: Optional[datetime] = None
    id_pdc_itinerance: List[str] = Field(min_length=1)
