"""QualiCharge prefect indicators tests: usage.

C2: Energy cumulate by operator.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore
from indicators.usage import c2  # type: ignore

from ..param_tests import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result for level [city, epci, dpt, reg]
N_LEVEL = [1, 10, 5, 34]
N_LEVEL_NATIONAL = 88

TIMESPAN = IndicatorTimeSpan(start=datetime(2024, 12, 24), period=IndicatorPeriod.DAY)
PARAMETERS_FLOW = [prm + (lvl,) for prm, lvl in zip(PARAM_FLOW, N_LEVEL, strict=True)]
PARAMETERS_VALUE = [prm + (lvl,) for prm, lvl in zip(PARAM_VALUE, N_LEVEL, strict=True)]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_VALUE)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    values = c2.get_values_for_targets.fn(db_connection, level, TIMESPAN, indexes)
    assert len(set(values["level_id"])) == len(indexes)
    assert int(values["value"].sum()) == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        c2.get_values_for_targets.fn(db_connection, Level.NATIONAL, TIMESPAN, [])


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_c2_for_level(db_connection, level, query, targets, expected):
    """Test the `c2_for_level` flow."""
    indicators = c2.c2_for_level(level, TIMESPAN, chunk_size=1000)
    # assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_c2_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `c2_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = c2.c2_for_level(level, TIMESPAN, chunk_size=chunk_size)
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


def test_flow_c2_national(db_connection):
    """Test the `c2_national` flow."""
    indicators = c2.c2_national(TIMESPAN)
    assert int(indicators["value"].sum()) == N_LEVEL_NATIONAL


def test_flow_c2_calculate(db_connection):
    """Test the `calculate` flow."""
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = c2.calculate(
        TIMESPAN, all_levels, create_artifact=True, format_pd=True
    )
    assert list(indicators["level"].unique()) == all_levels


# query used to get N_LEVEL
N_LEVEL_NAT = """
        SELECT
            sum(energy) / 1000.0 AS value
        FROM
            SESSION
            INNER JOIN statique ON point_de_charge_id = pdc_id
        WHERE
            START >= timestamp '2024-12-24'
            AND START < timestamp '2024-12-25'
"""
N_LEVEL_3 = """
        SELECT
            sum(energy) / 1000.0 AS value
        FROM
            Session
            INNER JOIN statique ON point_de_charge_id = pdc_id
            LEFT JOIN City ON City.code = code_insee_commune
            INNER JOIN Department ON City.department_id = Department.id
            INNER JOIN Region ON Department.region_id = Region.id
        WHERE
            START >= timestamp '2024-12-24'
            AND START < timestamp '2024-12-25'
            AND region.code IN ('11', '84', '75')
"""
