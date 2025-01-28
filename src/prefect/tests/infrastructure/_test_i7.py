"""QualiCharge prefect indicators tests: infrastructure.

I7: installed power.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.infrastructure import i7  # type: ignore
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore

# expected result
N_LEVEL = [18998, 137622, 132546, 664670]
N_DPTS = 109
TIMESPAN = IndicatorTimeSpan(start=datetime.now(), period=IndicatorPeriod.DAY)


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
    values = i7.get_values_for_targets.fn(db_connection, level, indexes)
    assert len(values) == len(indexes)
    assert int(values["value"].sum()) == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        i7.get_values_for_targets.fn(db_connection, Level.NATIONAL, [])


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_i7_for_level(db_connection, level, query, targets, expected):
    """Test the `i7_for_level` flow."""
    indicators = i7.i7_for_level(level, TIMESPAN, chunk_size=1000)
    assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_i7_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `i7_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = i7.i7_for_level(level, TIMESPAN, chunk_size=chunk_size)
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
    indicators = i7.i7_national(TIMESPAN)
    assert int(indicators.at[0, "value"]) == expected


def test_flow_i7_calculate(db_connection):
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
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = i7.calculate(TIMESPAN, all_levels, create_artifact=True)
    assert len(indicators) == expected
