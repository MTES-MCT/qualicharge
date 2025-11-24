"""QualiCharge prefect indicators tests: usage.

U13: cumulative power of POC in operation.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore
from indicators.types import Environment
from indicators.usage import u13  # type: ignore
from tests.parameters import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result for level [city, epci, dpt, reg]
N_LEVEL = [1164, 37208, 41978, 195354]
N_LEVEL_NATIONAL = 527061

TIMESPAN = IndicatorTimeSpan(start=datetime(2024, 12, 24), period=IndicatorPeriod.DAY)
PARAMETERS_FLOW = [prm + (lvl,) for prm, lvl in zip(PARAM_FLOW, N_LEVEL, strict=True)]
PARAMETERS_VALUE = [prm + (lvl,) for prm, lvl in zip(PARAM_VALUE, N_LEVEL, strict=True)]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_VALUE)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    values = u13.get_values_for_targets.fn(level, TIMESPAN, indexes, Environment.TEST)
    assert len(values) == len(indexes)
    assert int(values["value"].sum()) == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        u13.get_values_for_targets.fn(Level.NATIONAL, TIMESPAN, [], Environment.TEST)


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_u13_for_level(db_connection, level, query, targets, expected):
    """Test the `u13_for_level` flow."""
    indicators = u13.u13_for_level(level, TIMESPAN, Environment.TEST, chunk_size=1000)
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_u13_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `u13_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = u13.u13_for_level(
        level, TIMESPAN, Environment.TEST, chunk_size=chunk_size
    )
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


def test_flow_u13_national(db_connection):
    """Test the `u13_national` flow."""
    indicators = u13.u13_national(TIMESPAN, Environment.TEST)
    assert int(indicators["value"].sum()) == N_LEVEL_NATIONAL


def test_flow_u13(db_connection):
    """Test the `u13` flow."""
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = u13.u13(
        Environment.TEST,
        all_levels,
        start=TIMESPAN.start,
        offset=0,
        period=TIMESPAN.period.value,
        create_artifact=True,
    )
    assert list(indicators["level"].unique()) == all_levels


def test_flow_u13_persistence(indicators_db_engine):
    """Test the `u13` flow."""
    indicators = u13.u13(
        Environment.TEST,
        [Level.NATIONAL],
        start=TIMESPAN.start,
        offset=0,
        period=TIMESPAN.period.value,
        persist=True,
    )

    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM test WHERE code = 'u13'")
        )
        assert result.one()[0] == len(indicators)
