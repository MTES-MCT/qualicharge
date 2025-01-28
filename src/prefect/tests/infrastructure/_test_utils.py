"""QualiCharge prefect indicators tests: infrastructure.

common tests for all indicators.
"""

import pytest  # type: ignore
from sqlalchemy import text

from indicators.infrastructure import i1  # type: ignore
from indicators.models import Level  # type: ignore

PARAMETERS_GET_TARGETS = [
    (Level.CITY, 35074),
    (Level.DEPARTMENT, 109),
    (Level.EPCI, 1255),
    (Level.REGION, 26),
]


def test_task_get_database_engine():
    """Test the `get_database_engine` task."""
    engine = i1.get_database_engine.fn()
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.first()[0] == 1


@pytest.mark.parametrize("level,expected", PARAMETERS_GET_TARGETS)
def test_task_get_targets_for_level(db_connection, level, expected):
    """Test the `get_targets_for_level` task."""
    assert len(i1.get_targets_for_level.fn(db_connection, level)) == expected


def test_task_get_targets_for_level_unexpected_level(db_connection):
    """Test the `get_targets_for_level` task (unexpected level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        i1.get_targets_for_level.fn(db_connection, Level.NATIONAL)
