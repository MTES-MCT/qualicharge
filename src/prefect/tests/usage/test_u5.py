"""QualiCharge prefect indicators tests: usage.

U5: Hourly distribution of sessions (number).
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore
from indicators.usage import u5  # type: ignore

from ..param_tests import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result for level [city, epci, dpt, reg]
N_LEVEL = [32, 307, 172, 1055]
N_LEVEL_NATIONAL = 2718

TIMESPAN = IndicatorTimeSpan(start=datetime(2024, 12, 24), period=IndicatorPeriod.DAY)
PARAMETERS_FLOW = [prm + (lvl,) for prm, lvl in zip(PARAM_FLOW, N_LEVEL, strict=True)]
PARAMETERS_VALUE = [prm + (lvl,) for prm, lvl in zip(PARAM_VALUE, N_LEVEL, strict=True)]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_VALUE)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    ses_by_hour = u5.get_values_for_targets.fn(db_connection, level, TIMESPAN, indexes)
    assert len(set(ses_by_hour["level_id"])) == len(indexes)
    assert ses_by_hour["value"].sum() == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        u5.get_values_for_targets.fn(db_connection, Level.NATIONAL, TIMESPAN, [])


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_u5_for_level(db_connection, level, query, targets, expected):
    """Test the `u5_for_level` flow."""
    indicators = u5.u5_for_level(level, TIMESPAN, chunk_size=1000)
    # assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_u5_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `u5_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = u5.u5_for_level(level, TIMESPAN, chunk_size=chunk_size)
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


def test_flow_u5_national(db_connection):
    """Test the `u5_national` flow."""
    indicators = u5.u5_national(TIMESPAN)
    assert indicators["value"].sum() == N_LEVEL_NATIONAL


def test_flow_u5_calculate(db_connection):
    """Test the `calculate` flow."""
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = u5.calculate(
        TIMESPAN, all_levels, create_artifact=True, format_pd=True
    )
    assert list(indicators["level"].unique()) == all_levels


# query used to get N_LEVEL
N_LEVEL_NAT = """

"""
N_LEVEL_3 = """

"""
