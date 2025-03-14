"""QualiCharge prefect indicators tests: extract.

E4: the list of points of charge in activity.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.extract import e4
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level, PeriodDuration
from indicators.types import Environment
from tests.parameters import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result
N_LEVEL = [51, 520, 372, 1963]
N_LEVEL_NATIONAL = 5278
N_DPTS = 109
N_NAT_REG_DPT_EPCI_CITY = 36465

TIMESPAN = IndicatorTimeSpan(start=datetime(2024, 12, 24), period=IndicatorPeriod.DAY)
TIMESPAN_QUERY = IndicatorTimeSpan(
    start=TIMESPAN.start - PeriodDuration.MONTH.value,
    period=IndicatorPeriod.MONTH,
)
PARAMETERS_FLOW = [prm + (lvl,) for prm, lvl in zip(PARAM_FLOW, N_LEVEL, strict=True)]
PARAMETERS_VALUE = [prm + (lvl,) for prm, lvl in zip(PARAM_VALUE, N_LEVEL, strict=True)]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_VALUE)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    poc_extract = e4.get_values_for_targets.fn(
        level, TIMESPAN, indexes, Environment.TEST
    )
    assert len(set(poc_extract["level_id"])) == len(indexes)
    # assert poc_extract["value"].sum() == expected


def test_task_get_values_for_target_unexpected_level():
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        e4.get_values_for_targets.fn(Level.NATIONAL, TIMESPAN, [], Environment.TEST)


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_e4_for_level(db_connection, level, query, targets, expected):
    """Test the `e4_for_level` flow."""
    indicators = e4.e4_for_level(level, TIMESPAN, Environment.TEST, chunk_size=1000)
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_e4_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `e4_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = e4.e4_for_level(
        level, TIMESPAN, Environment.TEST, chunk_size=chunk_size
    )
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


def test_flow_e4_national():
    """Test the `e4_national` flow."""
    indicators = e4.e4_national(TIMESPAN, TIMESPAN_QUERY, Environment.TEST)
    assert int(indicators["value"].sum()) == N_LEVEL_NATIONAL


def test_flow_e4_calculate():
    """Test the `calculate` flow."""
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = e4.calculate(
        Environment.TEST,
        all_levels,
        TIMESPAN.start,
        TIMESPAN.period.value,
        create_artifact=False,
    )
    assert list(indicators["level"].unique()) == all_levels


def test_flow_calculate_persistence(indicators_db_engine):
    """Test the `calculate` flow."""
    indicators = e4.calculate(
        Environment.TEST,
        [Level.NATIONAL],
        TIMESPAN.start,
        TIMESPAN.period.value,
        persist=True,
    )

    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test WHERE code = 'e4'"))
        assert result.one()[0] == len(indicators)
