"""QualiCharge prefect indicators tests: infrastructure.

T1: the number of publicly open points of charge by power level.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.infrastructure import t1  # type: ignore
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore
from indicators.types import Environment

from ..parameters import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result
N_LEVEL = [56, 2484, 4242, 12147]
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
    poc_by_power = t1.get_values_for_targets.fn(level, indexes, Environment.TEST)
    assert len(set(poc_by_power["level_id"])) == len(indexes)
    assert poc_by_power["value"].sum() == expected


def test_task_get_values_for_target_unexpected_level():
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        t1.get_values_for_targets.fn(Level.NATIONAL, [], Environment.TEST)


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_t1_for_level(db_connection, level, query, targets, expected):
    """Test the `t1_for_level` flow."""
    indicators = t1.t1_for_level(level, TIMESPAN, Environment.TEST, chunk_size=1000)
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_t1_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `t1_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = t1.t1_for_level(
        level, TIMESPAN, Environment.TEST, chunk_size=chunk_size
    )
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


def test_flow_t1_national(db_connection):
    """Test the `t1_national` flow."""
    query = "SELECT COUNT(*) FROM PointDeCharge WHERE puissance_nominale::numeric >= 0"
    expected = db_connection.execute(text(query)).scalars().one()
    indicators = t1.t1_national(TIMESPAN, Environment.TEST)
    assert indicators["value"].sum() == expected


def test_flow_t1():
    """Test the `t1` flow."""
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = t1.t1(
        Environment.TEST,
        all_levels,
        TIMESPAN.start,
        TIMESPAN.period,
        create_artifact=True,
    )
    assert list(indicators["level"].unique()) == all_levels


def test_flow_t1_persistence(indicators_db_engine):
    """Test the `t1` flow."""
    indicators = t1.t1(
        Environment.TEST,
        [Level.NATIONAL],
        TIMESPAN.start,
        TIMESPAN.period,
        persist=True,
    )

    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test WHERE code = 't1'"))
        assert result.one()[0] == len(indicators)
