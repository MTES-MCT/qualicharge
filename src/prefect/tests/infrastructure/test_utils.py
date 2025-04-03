"""QualiCharge prefect indicators tests: infrastructure.

common tests for all indicators.
"""

from datetime import datetime

import pytest  # type: ignore

from indicators.infrastructure import i1
from indicators.models import IndicatorPeriod, Level
from indicators.types import Environment
from indicators.utils import get_period_start_from_pit

PARAMETERS_GET_TARGETS = [
    (Level.CITY, 35074),
    (Level.DEPARTMENT, 109),
    (Level.EPCI, 1255),
    (Level.REGION, 26),
]


@pytest.mark.parametrize("level,expected", PARAMETERS_GET_TARGETS)
def test_task_get_targets_for_level(level, expected):
    """Test the `get_targets_for_level` task."""
    assert len(i1.get_targets_for_level.fn(level, Environment.TEST)) == expected


def test_task_get_targets_for_level_unexpected_level():
    """Test the `get_targets_for_level` task (unexpected level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        i1.get_targets_for_level.fn(Level.NATIONAL, Environment.TEST)


def test_get_period_start_from_pit():
    """Test the 'get_period_start_from_pit' function."""
    tst = datetime(2024, 1, 10)
    assert get_period_start_from_pit(tst, -1, IndicatorPeriod.MONTH) == datetime(
        2023, 12, 1
    )
    assert get_period_start_from_pit(tst, -2, IndicatorPeriod.MONTH) == datetime(
        2023, 11, 1
    )
    assert get_period_start_from_pit(tst, -1, IndicatorPeriod.QUARTER) == datetime(
        2023, 10, 1
    )
    assert get_period_start_from_pit(tst, -2, IndicatorPeriod.QUARTER) == datetime(
        2023, 7, 1
    )
    assert get_period_start_from_pit(tst, -1, IndicatorPeriod.WEEK) == datetime(
        2024, 1, 1
    )
    assert get_period_start_from_pit(tst, -2, IndicatorPeriod.WEEK) == datetime(
        2023, 12, 25
    )
    assert get_period_start_from_pit(tst, 0, IndicatorPeriod.DAY) == datetime(
        2024, 1, 10
    )
    assert get_period_start_from_pit(tst, -1, IndicatorPeriod.DAY) == datetime(
        2024, 1, 9
    )
    assert get_period_start_from_pit(tst, -1, IndicatorPeriod.HOUR) == datetime(
        2024, 1, 9, 23
    )
    assert get_period_start_from_pit(tst, -2, IndicatorPeriod.HOUR) == datetime(
        2024, 1, 9, 22
    )
    assert get_period_start_from_pit(tst, -1, IndicatorPeriod.YEAR) == datetime(
        2023, 1, 1
    )
    assert get_period_start_from_pit(tst, -2, IndicatorPeriod.YEAR) == datetime(
        2022, 1, 1
    )
    tst = datetime(2024, 1, 8)
    assert get_period_start_from_pit(tst, -1, IndicatorPeriod.WEEK) == datetime(
        2024, 1, 1
    )
    assert get_period_start_from_pit(tst, -2, IndicatorPeriod.WEEK) == datetime(
        2023, 12, 25
    )
