"""QualiCharge prefect indicators tests: infrastructure.

I4: the number of publicly open points of charge.
"""

import pandas as pd  # type: ignore
import pytest  # type: ignore
from sqlalchemy import text

from indicators.infrastructure import i4  # type: ignore
from indicators.models import IndicatorPeriod, Level  # type: ignore

# expected result
N_LEVEL = [65, 1073, 421, 3793]
N_DPTS = 109

PERIOD = IndicatorPeriod.DAY
PARAMETERS_CHUNK = [10, 50, 100, 500]
PARAMETERS_FLOW = [
    (
        Level.CITY,
        "SELECT COUNT(*) FROM City",
        ["75056", "13055", "69123"],
        N_LEVEL[0],
    ),
    (
        Level.EPCI,
        "SELECT COUNT(*) FROM EPCI",
        ["200054781", "200054807", "200046977"],
        N_LEVEL[1],
    ),
    (
        Level.DEPARTMENT,
        "SELECT COUNT(*) FROM Department",
        ["59", "75", "13"],
        N_LEVEL[2],
    ),
    (
        Level.REGION,
        "SELECT COUNT(*) FROM Region",
        ["11", "84", "75"],
        N_LEVEL[3],
    ),
]
PARAMETERS_GET_VALUES = [
    (
        Level.CITY,
        "SELECT id FROM City WHERE name IN ('Paris', 'Marseille', 'Lyon')",
        N_LEVEL[0],
    ),
    (
        Level.EPCI,
        "SELECT id FROM EPCI WHERE code IN ('200054781', '200054807', '200046977')",
        N_LEVEL[1],
    ),
    (
        Level.DEPARTMENT,
        "SELECT id FROM Department WHERE code IN ('59', '75', '13')",
        N_LEVEL[2],
    ),
    (
        Level.REGION,
        "SELECT id FROM Region WHERE code IN ('11', '84', '75')",
        N_LEVEL[3],
    ),
]


@pytest.mark.parametrize("level,query,expected", PARAMETERS_GET_VALUES)
def test_task_get_values_for_target(db_connection, level, query, expected):
    """Test the `get_values_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    values = i4.get_values_for_targets.fn(db_connection, level, indexes)
    assert len(values) == len(indexes)
    assert values["value"].sum() == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        i4.get_values_for_targets.fn(db_connection, Level.NATIONAL, [])


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_i4_for_level(db_connection, level, query, targets, expected):
    """Test the `i4_for_level` flow."""
    now = pd.Timestamp.now()
    indicators = i4.i4_for_level(level, PERIOD, now, chunk_size=1000)
    assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_i4_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `i4_for_level` flow with various chunk sizes."""
    now = pd.Timestamp.now()
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = i4.i4_for_level(level, PERIOD, now, chunk_size=chunk_size)
    assert len(indicators) == N_DPTS
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


def test_flow_i4_national(db_connection):
    """Test the `i4_national` flow."""
    result = db_connection.execute(text("SELECT COUNT(id) FROM Station"))
    expected = result.scalars().one()
    indicators = i4.i4_national(PERIOD, pd.Timestamp.now())
    assert indicators.at[0, "value"] == expected


def test_flow_i4_calculate(db_connection):
    """Test the `calculate` flow."""
    result = db_connection.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) AS region_count FROM Region),
                (SELECT COUNT(*) AS department_count FROM Department),
                (SELECT COUNT(*) AS epci_count FROM EPCI),
                (SELECT COUNT(*) AS city_count FROM City)
            """
        )
    )
    expected = sum(result.one()) + 1
    indicators = i4.calculate(PERIOD, create_artifact=True)
    assert len(indicators) == expected
