"""QualiCharge prefect indicators tests: usage.

U12: the number of POC in operation.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore
from indicators.types import Environment
from indicators.usage import u12  # type: ignore
from tests.parameters import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result for level [city, epci, dpt, reg]
N_LEVEL = [7, 299, 550, 1589]
N_LEVEL_NATIONAL = 3857

TIMESPAN = IndicatorTimeSpan(start=datetime(2024, 12, 24), period=IndicatorPeriod.DAY)
PARAMETERS_FLOW = [prm + (lvl,) for prm, lvl in zip(PARAM_FLOW, N_LEVEL, strict=True)]
PARAMETERS_VALUE = [prm + (lvl,) for prm, lvl in zip(PARAM_VALUE, N_LEVEL, strict=True)]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_VALUE)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    poc_by_power = u12.get_values_for_targets.fn(
        level, TIMESPAN, indexes, Environment.TEST
    )
    assert len(set(poc_by_power["level_id"])) == len(indexes)
    assert poc_by_power["value"].sum() == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        u12.get_values_for_targets.fn(Level.NATIONAL, TIMESPAN, [], Environment.TEST)


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_u12_for_level(db_connection, level, query, targets, expected):
    """Test the `u12_for_level` flow."""
    indicators = u12.u12_for_level(level, TIMESPAN, Environment.TEST, chunk_size=1000)
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_u12_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `u12_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = u12.u12_for_level(
        level, TIMESPAN, Environment.TEST, chunk_size=chunk_size
    )
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


def test_flow_u12_national(db_connection):
    """Test the `u12_national` flow."""
    indicators = u12.u12_national(TIMESPAN, Environment.TEST)
    assert indicators["value"].sum() == N_LEVEL_NATIONAL


def test_flow_u12(db_connection):
    """Test the `u12` flow."""
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = u12.u12(
        Environment.TEST,
        all_levels,
        start=TIMESPAN.start,
        offset=0,
        period=TIMESPAN.period.value,
        create_artifact=True,
    )
    assert list(indicators["level"].unique()) == all_levels


def test_flow_u12_persistence(indicators_db_engine):
    """Test the `u12` flow."""
    indicators = u12.u12(
        Environment.TEST,
        [Level.NATIONAL],
        start=TIMESPAN.start,
        offset=0,
        period=TIMESPAN.period.value,
        persist=True,
    )
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM test WHERE code = 'u12'")
        )
        assert result.one()[0] == len(indicators)
