"""QualiCharge afirev models."""

from enum import StrEnum
from typing import List, Self

from pydantic import BaseModel, Field

from qualicharge.schemas.core import OperationalUnit
from qualicharge.schemas.core import (
    OperationalUnitStatusEnum as OUSEnum,
)
from qualicharge.schemas.core import (
    OperationalUnitTypeEnum as OUTEnum,
)


class AfirevPrefixStatusEnum(StrEnum):
    """AFIREV Prefix statuses."""

    ACTIVE = "ACTIVE"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    UNKNOWN = "UNKNOWN"


class AfirevPrefixTypeEnum(StrEnum):
    """AFIREV Prefix types."""

    BOTH = "BOTH"
    CHARGE = "CHARGE"
    MOBILITY = "MOBILITY"


AfirevPrefixStatusToOperationalUnit = {
    AfirevPrefixStatusEnum.ACTIVE: OUSEnum.ACTIVE,
    AfirevPrefixStatusEnum.AWAITING_PAYMENT: OUSEnum.AWAITING_PAYMENT,
    AfirevPrefixStatusEnum.INACTIVE: OUSEnum.INACTIVE,
    AfirevPrefixStatusEnum.SUSPENDED: OUSEnum.SUSPENDED,
    AfirevPrefixStatusEnum.UNKNOWN: None,
}

OperationalUnitStatusToAfirevPrefix = {
    v: k for k, v in AfirevPrefixStatusToOperationalUnit.items()
}

AfirevPrefixTypeToOperationalUnit = {
    AfirevPrefixTypeEnum.BOTH: OUTEnum.BOTH,
    AfirevPrefixTypeEnum.CHARGE: OUTEnum.CHARGING,
    AfirevPrefixTypeEnum.MOBILITY: OUTEnum.MOBILITY,
}

OperationalUnitTypeToAfirevPrefix = {
    v: k for k, v in AfirevPrefixTypeToOperationalUnit.items()
}


class AfirevPrefix(BaseModel):
    """AFIREV prefix."""

    prefixId: str = Field(pattern="^[A-Z]{2}[A-Z0-9]{3}$")
    name: str
    amenageurName: str | None
    exploitantName: str | None
    type: AfirevPrefixTypeEnum
    status: AfirevPrefixStatusEnum

    def to_operational_unit(self) -> OperationalUnit:
        """Convert prefix to an operational unit."""
        return OperationalUnit(
            code=self.prefixId,
            name=self.name,
            type=AfirevPrefixTypeToOperationalUnit[self.type],
            status=AfirevPrefixStatusToOperationalUnit[self.status],
            amenageur=self.amenageurName,
            exploitant=self.exploitantName,
        )

    @classmethod
    def from_operational_unit(cls, operational_unit: OperationalUnit) -> Self:
        """Create an AfirevPrefix instance from an operational unit."""
        return cls(
            prefixId=operational_unit.code,
            name=operational_unit.name,
            amenageurName=operational_unit.amenageur,
            exploitantName=operational_unit.exploitant,
            type=OperationalUnitTypeToAfirevPrefix[operational_unit.type],
            status=(
                OperationalUnitStatusToAfirevPrefix[operational_unit.status]
                if operational_unit.status
                else AfirevPrefixStatusEnum.UNKNOWN
            ),
        )


class AfirevPrefixAPIResponse(BaseModel):
    """AFIREV "/prefixes" API endpoint response."""

    data: List[AfirevPrefix]
    total: int
