"""QualiCharge prefect indicators: models."""

from datetime import datetime, timedelta
from enum import Enum, IntEnum
from typing import Optional

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel  # type: ignore


class Level(IntEnum):
    """Administrative levels."""

    NATIONAL = 0
    REGION = 1
    DEPARTMENT = 2
    EPCI = 3
    CITY = 4
    OU = 5  # Operational Unit
    AMENAGEUR = 6


class IndicatorPeriod(Enum):
    """Time-based indicator periods."""

    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    MONTH = "m"
    QUARTER = "q"
    YEAR = "y"

    @property
    def duration(self):
        """Time delta of the period."""
        return PeriodDuration[self.name].value


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


class IndicatorTimeSpan(BaseModel):
    """Time span of a period for an indicator."""

    period: IndicatorPeriod
    start: datetime


class PeriodDuration(Enum):
    """Represents the time delta of an IndicatorPeriod."""

    HOUR = timedelta(hours=1)
    DAY = timedelta(days=1)
    WEEK = timedelta(days=7)
    MONTH = relativedelta(months=1)
    QUARTER = relativedelta(months=3)
    YEAR = relativedelta(years=1)
