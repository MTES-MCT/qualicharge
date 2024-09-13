"""QualiCharge prefect indicators: models."""

from datetime import datetime
from enum import Enum, IntEnum
from typing import Optional

from pydantic import BaseModel


class Level(IntEnum):
    """Administrative levels."""

    NATIONAL = 0
    REGION = 1
    DEPARTMENT = 2
    EPCI = 3
    CITY = 4


class IndicatorPeriod(Enum):
    """Time-based indicator periods."""

    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    MONTH = "m"
    QUARTER = "q"
    YEAR = "y"


class Indicator(BaseModel):
    """Indicator result."""

    code: str
    level: Level
    target: Optional[str] = None
    period: IndicatorPeriod
    category: Optional[str] = None
    value: float
    extras: Optional[dict] = None
    timestamp: datetime
