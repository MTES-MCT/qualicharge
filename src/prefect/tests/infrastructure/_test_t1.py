"""QualiCharge prefect indicators tests: infrastructure.

T1: the number of publicly open points of charge by power level.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.infrastructure import t1  # type: ignore
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore

from ..param_tests import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result
N_LEVEL = [212, 2250, 1489, 8724]
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
    poc_by_power = t1.get_values_for_targets.fn(db_connection, level, indexes)
    assert len(set(poc_by_power["level_id"])) == len(indexes)
    assert poc_by_power["value"].sum() == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        t1.get_values_for_targets.fn(db_connection, Level.NATIONAL, [])


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_t1_for_level(db_connection, level, query, targets, expected):
    """Test the `t1_for_level` flow."""
    indicators = t1.t1_for_level(level, TIMESPAN, chunk_size=1000)
    # assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_t1_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `t1_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = t1.t1_for_level(level, TIMESPAN, chunk_size=chunk_size)
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


def test_flow_t1_national(db_connection):
    """Test the `t1_national` flow."""
    query = "SELECT COUNT(*) FROM PointDeCharge WHERE puissance_nominale::numeric >= 0"
    expected = db_connection.execute(text(query)).scalars().one()
    indicators = t1.t1_national(TIMESPAN)
    assert indicators["value"].sum() == expected


def test_flow_t1_calculate(db_connection):
    """Test the `calculate` flow."""
    """expected = sum(
        [
            t1.t1_for_level(Level.CITY, TIMESPAN, chunk_size=1000)["value"].sum(),
            t1.t1_for_level(Level.EPCI, TIMESPAN, chunk_size=1000)["value"].sum(),
            t1.t1_for_level(Level.DEPARTMENT, TIMESPAN, chunk_size=1000)["value"].sum(),
            t1.t1_for_level(Level.REGION, TIMESPAN, chunk_size=1000)["value"].sum(),
            t1.t1_national(TIMESPAN)["value"].sum(),
        ]
    )"""
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = t1.calculate(
        TIMESPAN, all_levels, create_artifact=True, format_pd=True
    )
    # assert indicators["value"].sum() == expected
    assert list(indicators["level"].unique()) == all_levels
