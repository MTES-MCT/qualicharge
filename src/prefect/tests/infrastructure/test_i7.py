"""QualiCharge prefect indicators tests: infrastructure.

I7: installed power.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.infrastructure import i7
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level
from indicators.types import Environment

from ..parameters import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result for level [city, epci, dpt, reg]
N_LEVEL = [8462, 293432, 317084, 1420791]
N_DPTS = 109
N_NAT_REG_DPT_EPCI_CITY = 36465

TIMESPAN = IndicatorTimeSpan(start=datetime.now(), period=IndicatorPeriod.DAY)
PARAMETERS_FLOW = [prm + (lvl,) for prm, lvl in zip(PARAM_FLOW, N_LEVEL, strict=True)]
PARAMETERS_VALUE = [prm + (lvl,) for prm, lvl in zip(PARAM_VALUE, N_LEVEL, strict=True)]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_VALUE)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    values = i7.get_values_for_targets.fn(level, indexes, Environment.TEST)
    assert len(values) == len(indexes)
    assert int(values["value"].sum()) == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        i7.get_values_for_targets.fn(Level.NATIONAL, [], Environment.TEST)


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_i7_for_level(db_connection, level, query, targets, expected):
    """Test the `i7_for_level` flow."""
    indicators = i7.i7_for_level(level, TIMESPAN, Environment.TEST, chunk_size=1000)
    assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_i7_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `i7_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = i7.i7_for_level(
        level, TIMESPAN, Environment.TEST, chunk_size=chunk_size
    )
    assert len(indicators) == N_DPTS
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


def test_flow_i7_national(db_connection):
    """Test the `i7_national` flow."""
    result = db_connection.execute(
        text("SELECT sum(puissance_nominale) FROM pointdecharge")
    )
    expected = int(result.scalars().one())
    indicators = i7.i7_national(TIMESPAN, Environment.TEST)
    assert int(indicators.at[0, "value"]) == expected


def test_flow_i7_calculate(db_connection):
    """Test the `calculate` flow."""
    expected = N_NAT_REG_DPT_EPCI_CITY
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = i7.calculate(
        Environment.TEST,
        all_levels,
        TIMESPAN.start,
        TIMESPAN.period.value,
        create_artifact=True,
    )
    assert len(indicators) == expected


def test_flow_calculate_persistence(indicators_db_engine):
    """Test the `calculate` flow."""
    indicators = i7.calculate(
        Environment.TEST,
        [Level.NATIONAL],
        TIMESPAN.start,
        TIMESPAN.period.value,
        persist=True,
    )
    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test WHERE code = 'i7'"))
        assert result.one()[0] == len(indicators)
