"""QualiCharge afirev models."""

from enum import StrEnum
from typing import List

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


class AfirevPrefixTypeEnum(StrEnum):
    """AFIREV Prefix types."""

    BOTH = "BOTH"
    CHARGE = "CHARGE"
    MOBILITY = "MOBILITY"


class AfirevPrefix(BaseModel):
    """AFIREV prefix."""

    prefixId: str = Field(pattern="^[A-Z]{2}[A-Z0-9]{3}$")
    name: str
    amenageurName: str
    exploitantName: str
    type: AfirevPrefixTypeEnum
    status: AfirevPrefixStatusEnum

    def to_operational_unit(self):
        """Convert prefix to an operational unit."""
        types_correspondance = {
            AfirevPrefixTypeEnum.BOTH: OUTEnum.BOTH,
            AfirevPrefixTypeEnum.CHARGE: OUTEnum.CHARGING,
            AfirevPrefixTypeEnum.MOBILITY: OUTEnum.MOBILITY,
        }
        statuses_correspondance = {
            AfirevPrefixStatusEnum.ACTIVE: OUSEnum.ACTIVE,
            AfirevPrefixStatusEnum.AWAITING_PAYMENT: OUSEnum.AWAITING_PAYMENT,
            AfirevPrefixStatusEnum.INACTIVE: OUSEnum.INACTIVE,
            AfirevPrefixStatusEnum.SUSPENDED: OUSEnum.SUSPENDED,
        }
        return OperationalUnit(
            code=self.prefixId,
            name=self.name,
            type=types_correspondance[self.type],
            status=statuses_correspondance[self.status],
            amenageur=self.amenageurName,
            exploitant=self.exploitantName,
        )


class AfirevPrefixAPIResponse(BaseModel):
    """AFIREV "/prefixes" API endpoint response."""

    data: List[AfirevPrefix]
    total: int
