"""QualiCharge tariff models."""

from datetime import date, time
from enum import StrEnum
from typing import Annotated, Any, List, Literal, Optional, Union
from uuid import UUID

from annotated_types import Ge, MaxLen
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)
from pydantic.types import AwareDatetime
from sqlmodel import SQLModel
from typing_extensions import Self

from .fields import IdPdcItinerance
from .utils import PaginatedListResponse

# Current models implement the following specification:
#
# https://github.com/loco-philippe/IRVE/blob/main/OCPI/source/schema.json


class TariffPayloadModel(BaseModel):
    """Base model for tariff payload fragments."""

    model_config = ConfigDict(extra="allow")


class TariffDimensionTypeEnum(StrEnum):
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


class TariffTypeEnum(StrEnum):
    """OCPI tariff type."""

    AD_HOC_PAYMENT = "AD_HOC_PAYMENT"
    PROFILE_CHEAP = "PROFILE_CHEAP"
    PROFILE_FAST = "PROFILE_FAST"
    PROFILE_GREEN = "PROFILE_GREEN"
    REGULAR = "REGULAR"


class TariffAltText(TariffPayloadModel):
    """Localized tariff display text."""

    language: str
    text: str


class PriceLimit(TariffPayloadModel):
    """OCPI 2.3 display price."""

    before_taxes: float
    after_taxes: Optional[float] = None


class Price(TariffPayloadModel):
    """OCPI 2.2 price with VAT split."""

    excl_vat: float
    incl_vat: Optional[float] = None


class PriceComponent(TariffPayloadModel):
    """A tariff price component."""

    type: TariffDimensionTypeEnum
    price: Annotated[float, Ge(0.0)]
    vat: Optional[Literal[20]] = None
    step_size: Optional[Annotated[int, Ge(1)]] = None


class TariffRestrictions(TariffPayloadModel):
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


class TariffElement(TariffPayloadModel):
    """A tariff element, composed of prices and optional restrictions."""

    price_components: List[PriceComponent] = Field(min_length=1)
    restrictions: Optional[TariffRestrictions] = None


class TariffObject(TariffPayloadModel):
    """Internal tariff object compatible with a subset of OCPI."""

    country_code: Annotated[str, StringConstraints(min_length=2, max_length=2)]
    party_id: Annotated[str, StringConstraints(min_length=3, max_length=3)]
    id: Annotated[str, StringConstraints(max_length=36)]
    type: Optional[Literal[TariffTypeEnum.AD_HOC_PAYMENT]] = None
    currency: Optional[Literal["EUR"]] = None
    elements: List[TariffElement] = Field(min_length=1)
    tariff_alt_text: Optional[List[TariffAltText]] = None
    tariff_alt_url: Optional[Annotated[HttpUrl, MaxLen(255)]] = None
    start_date_time: Optional[AwareDatetime] = None
    end_date_time: Optional[AwareDatetime] = None
    last_updated: AwareDatetime
    tax_included: Optional[Literal[TaxIncludedEnum.YES, TaxIncludedEnum.NO]] = None
    min_price: Optional[Union[Price, PriceLimit]] = None
    max_price: Optional[Union[Price, PriceLimit]] = None

    @property
    def tariff_application_date(self) -> AwareDatetime:
        """Return the first date from which the tariff can be applied."""
        return max(self.start_date_time or self.last_updated, self.last_updated)

    @property
    def tariff_id(self) -> str:
        """Return the functional OCPI tariff identifier."""
        return self.country_code + self.party_id + self.id

    @property
    def ocpi_version(self) -> str:
        """Infer the OCPI version from tax_included field support."""
        if self.tax_included is not None:
            return "2.3"
        return "2.2"

    @property
    def is_tax_included(self) -> bool:
        """Return whether tariff prices include taxes."""
        return (
            self.tax_included is not None and self.tax_included == TaxIncludedEnum.YES
        )

    @model_validator(mode="after")
    def check_application_dates(self) -> Self:
        """Ensure tariff start/end dates are consistent."""
        if (
            self.start_date_time is not None
            and self.end_date_time is not None
            and self.start_date_time > self.end_date_time
        ):
            raise ValueError("A tariff cannot start after it has ended.")
        if self.end_date_time is not None and self.last_updated > self.end_date_time:
            raise ValueError(
                f"Tariff {self.tariff_id} cannot end before his last updated time."
            )
        return self


class TariffCreate(SQLModel):
    """Tariff creation payload."""

    targets: List[IdPdcItinerance] = Field(min_length=1)
    tariff: TariffObject


class TariffRead(SQLModel):
    """Tariff read payload."""

    id: str
    original_id: str
    original_last_updated: AwareDatetime
    raw: dict[str, Any]
    start: AwareDatetime
    end: Optional[AwareDatetime]
    id_pdc_itinerance: List[IdPdcItinerance] = Field(default_factory=list)


PaginatedTariffListResponse = PaginatedListResponse[TariffRead]


class TariffChargePointUpdate(BaseModel):
    """Payload to apply a tariff to a charge point."""

    tariff_id: UUID


class PointDeChargeTariffCreate(SQLModel):
    """Associate a tariff with charge points."""

    original_id: str
    original_last_updated: AwareDatetime
    id_pdc_itinerance: List[IdPdcItinerance] = Field(min_length=1)
