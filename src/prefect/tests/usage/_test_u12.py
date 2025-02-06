"""QualiCharge prefect indicators tests: usage.

U12: the number of POC in operation.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore
from indicators.usage import u12  # type: ignore

from ..param_tests import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result for level [city, epci, dpt, reg]
N_LEVEL = [36, 386, 261, 1462]
N_LEVEL_NATIONAL = 3851

TIMESPAN = IndicatorTimeSpan(start=datetime(2024, 12, 24), period=IndicatorPeriod.DAY)
PARAMETERS_FLOW = [prm + (lvl,) for prm, lvl in zip(PARAM_FLOW, N_LEVEL, strict=True)]
PARAMETERS_VALUE = [prm + (lvl,) for prm, lvl in zip(PARAM_VALUE, N_LEVEL, strict=True)]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_VALUE)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    poc_by_power = u12.get_values_for_targets.fn(
        db_connection, level, TIMESPAN, indexes
    )
    assert len(set(poc_by_power["level_id"])) == len(indexes)
    assert poc_by_power["value"].sum() == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        u12.get_values_for_targets.fn(db_connection, Level.NATIONAL, TIMESPAN, [])


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_u12_for_level(db_connection, level, query, targets, expected):
    """Test the `u12_for_level` flow."""
    indicators = u12.u12_for_level(level, TIMESPAN, chunk_size=1000)
    # assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_u12_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `u12_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = u12.u12_for_level(level, TIMESPAN, chunk_size=chunk_size)
    # assert len(indicators) == N_DPTS
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


def test_flow_u12_national(db_connection):
    """Test the `u12_national` flow."""
    indicators = u12.u12_national(TIMESPAN)
    assert indicators["value"].sum() == N_LEVEL_NATIONAL


def test_flow_u12_calculate(db_connection):
    """Test the `calculate` flow."""
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = u12.calculate(
        TIMESPAN, all_levels, create_artifact=True, format_pd=True
    )
    assert list(indicators["level"].unique()) == all_levels


# query used to get N_LEVEL
