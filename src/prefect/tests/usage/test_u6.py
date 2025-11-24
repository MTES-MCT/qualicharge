"""QualiCharge prefect indicators tests: usage.

U6: session duration by power category.

# query used to get N_LEVEL_NAT

WITH
  sessionf AS (
    SELECT
      point_de_charge_id,
      sum(SESSION.end - SESSION.start) AS duree_pdc
    FROM
      SESSION
    WHERE
      START >= date '2024-12-24'
      AND START < date '2024-12-25'
    GROUP BY
      point_de_charge_id
  )
SELECT
  extract(
    'epoch'
    FROM
      sum(duree_pdc)
  ) / 3600.0 AS duree
FROM
  sessionf
  INNER JOIN PointDeCharge ON sessionf.point_de_charge_id = PointDeCharge.id
  LEFT JOIN station ON station_id = station.id
  LEFT JOIN localisation ON localisation_id = localisation.id
  LEFT JOIN city ON city.code = code_insee_commune
  LEFT JOIN department ON city.department_id = department.id
  LEFT JOIN region ON department.region_id = region.id

# query used to get N_LEVEL_3

WITH
  sessionf AS (
    SELECT
      point_de_charge_id,
      sum(SESSION.end - SESSION.start) AS duree_pdc
    FROM
      SESSION
    WHERE
      START >= date '2024-12-24'
      AND START < date '2024-12-25'
    GROUP BY
      point_de_charge_id
  )
SELECT
  extract(
    'epoch'
    FROM
      sum(duree_pdc)
  ) / 3600.0 AS duree
FROM
  sessionf
  INNER JOIN PointDeCharge ON sessionf.point_de_charge_id = PointDeCharge.id
  LEFT JOIN station ON station_id = station.id
  LEFT JOIN localisation ON localisation_id = localisation.id
  LEFT JOIN city ON city.code = code_insee_commune
  LEFT JOIN department ON city.department_id = department.id
  LEFT JOIN region ON department.region_id = region.id
WHERE
  region.code IN ('11', '84', '75')
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore
from indicators.types import Environment
from indicators.usage import u6  # type: ignore
from tests.parameters import (
    PARAM_FLOW,
    PARAM_VALUE,
    PARAMETERS_CHUNK,
)

# expected result for level [city, epci, dpt, reg]
N_LEVEL = [5, 106, 205, 644]
N_LEVEL_NATIONAL = 1427

TIMESPAN = IndicatorTimeSpan(start=datetime(2024, 12, 24), period=IndicatorPeriod.DAY)
PARAMETERS_FLOW = [prm + (lvl,) for prm, lvl in zip(PARAM_FLOW, N_LEVEL, strict=True)]
PARAMETERS_VALUE = [prm + (lvl,) for prm, lvl in zip(PARAM_VALUE, N_LEVEL, strict=True)]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_VALUE)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    values = u6.get_values_for_targets.fn(level, TIMESPAN, indexes, Environment.TEST)
    assert len(set(values["level_id"])) == len(indexes)
    assert int(values["value"].sum()) == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        u6.get_values_for_targets.fn(Level.NATIONAL, TIMESPAN, [], Environment.TEST)


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_u6_for_level(db_connection, level, query, targets, expected):
    """Test the `u6_for_level` flow."""
    indicators = u6.u6_for_level(level, TIMESPAN, Environment.TEST, chunk_size=1000)
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_u6_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `u6_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = u6.u6_for_level(
        level, TIMESPAN, Environment.TEST, chunk_size=chunk_size
    )
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


def test_flow_u6_national(db_connection):
    """Test the `u6_national` flow."""
    indicators = u6.u6_national(TIMESPAN, Environment.TEST)
    assert int(indicators["value"].sum()) == N_LEVEL_NATIONAL


def test_flow_u6(db_connection):
    """Test the `u6` flow."""
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = u6.u6(
        Environment.TEST,
        all_levels,
        start=TIMESPAN.start,
        offset=0,
        period=TIMESPAN.period.value,
        create_artifact=True,
    )
    assert list(indicators["level"].unique()) == all_levels


def test_flow_u6_persistence(indicators_db_engine):
    """Test the `u6` flow."""
    indicators = u6.u6(
        Environment.TEST,
        [Level.NATIONAL],
        start=TIMESPAN.start,
        offset=0,
        period=TIMESPAN.period.value,
        persist=True,
    )

    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test WHERE code = 'u6'"))
        assert result.one()[0] == len(indicators)
