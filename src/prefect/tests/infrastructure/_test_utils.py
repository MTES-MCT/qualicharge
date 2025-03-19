"""QualiCharge prefect indicators tests: infrastructure.

common tests for all indicators.
"""

import pytest  # type: ignore

from indicators.infrastructure import i1  # type: ignore
from indicators.models import Level
from indicators.types import Environment  # type: ignore

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
