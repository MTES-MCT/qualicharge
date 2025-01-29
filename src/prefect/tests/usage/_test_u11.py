"""QualiCharge prefect indicators tests: usage.

U11: the number of successful sessions.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore
from indicators.usage import u11  # type: ignore

from ..param_tests import (
    N_DPTS,
    N_NAT_REG_DPT_EPCI_CITY,
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result for level [city, epci, dpt, reg]
N_LEVEL = [32, 301, 166, 1031]
N_LEVEL_NATIONAL = 2639

TIMESPAN = IndicatorTimeSpan(start=datetime(2024, 12, 24), period=IndicatorPeriod.DAY)
PARAMETERS_FLOW = [prm + (lvl,) for prm, lvl in zip(PARAM_FLOW, N_LEVEL, strict=True)]
PARAMETERS_VALUE = [prm + (lvl,) for prm, lvl in zip(PARAM_VALUE, N_LEVEL, strict=True)]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_VALUE)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    values = u11.get_values_for_targets.fn(db_connection, level, TIMESPAN, indexes)
    assert len(values) == len(indexes)
    assert values["value"].sum() == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        u11.get_values_for_targets.fn(db_connection, Level.NATIONAL, TIMESPAN, [])


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_u11_for_level(db_connection, level, query, targets, expected):
    """Test the `u11_for_level` flow."""
    indicators = u11.u11_for_level(level, TIMESPAN, chunk_size=1000)
    assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_u11_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `u11_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = u11.u11_for_level(level, TIMESPAN, chunk_size=chunk_size)
    assert len(indicators) == N_DPTS
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


def test_flow_u11_national(db_connection):
    """Test the `u11_national` flow."""
    indicators = u11.u11_national(TIMESPAN)
    assert indicators.at[0, "value"] == N_LEVEL_NATIONAL


def test_flow_u11_calculate(db_connection):
    """Test the `calculate` flow."""
    expected = N_NAT_REG_DPT_EPCI_CITY
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = u11.calculate(TIMESPAN, all_levels, create_artifact=True)
    assert len(indicators) == expected


# query used to get N_LEVEL
N_LEVEL_NAT = """
SELECT
  count(*) AS VALUE
FROM
  SESSION
WHERE
  START >= timestamp '2024-12-24'
  AND START < timestamp '2024-12-25'
  AND energy > 0.5
  AND SESSION.end - SESSION.start > '3 minutes'::interval
"""
N_LEVEL_3 = """
SELECT
  count(*) AS VALUE
FROM
  SESSION
  INNER JOIN PointDeCharge ON point_de_charge_id = PointDeCharge.id
  LEFT JOIN Station ON station_id = Station.id
  LEFT JOIN Localisation ON localisation_id = Localisation.id
  LEFT JOIN City ON City.code = code_insee_commune
  INNER JOIN Department ON City.department_id = Department.id
  INNER JOIN Region ON Department.region_id = Region.id
WHERE
  START >= timestamp '2024-12-24'
  AND START < timestamp '2024-12-25'
  AND energy > 0.5
  AND SESSION.end - SESSION.start > '3 minutes'::interval
  AND region.code IN ('11', '84', '75')"""
