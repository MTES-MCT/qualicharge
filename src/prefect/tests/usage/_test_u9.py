"""QualiCharge prefect indicators tests: usage.

U9: energy by power level.
"""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text

from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level  # type: ignore
from indicators.usage import u9  # type: ignore

# expected result for level [city, epci, dpt, reg, nat]
N_LEVEL = [1150, 10235, 5489, 34639, 88135]
N_DPTS = 109
N_NAT_REG_DPT_EPCI_CITY = 36465

TIMESPAN = IndicatorTimeSpan(start=datetime(2024, 12, 24), period=IndicatorPeriod.DAY)

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
    values = u9.get_values_for_targets.fn(db_connection, level, TIMESPAN, indexes)
    assert len(set(values["level_id"])) == len(indexes)
    assert int(values["value"].sum()) == expected


def test_task_get_values_for_target_unexpected_level(db_connection):
    """Test the `get_values_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        u9.get_values_for_targets.fn(db_connection, Level.NATIONAL, TIMESPAN, [])


@pytest.mark.parametrize("level,query,targets,expected", PARAMETERS_FLOW)
def test_flow_u9_for_level(db_connection, level, query, targets, expected):
    """Test the `u9_for_level` flow."""
    indicators = u9.u9_for_level(level, TIMESPAN, chunk_size=1000)
    # assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_u9_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `u9_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    indicators = u9.u9_for_level(level, TIMESPAN, chunk_size=chunk_size)
    # assert len(indicators) == N_DPTS
    assert (
        int(indicators.loc[indicators["target"].isin(targets), "value"].sum())
        == expected
    )


def test_flow_u9_national(db_connection):
    """Test the `u9_national` flow."""
    indicators = u9.u9_national(TIMESPAN)
    assert int(indicators["value"].sum()) == N_LEVEL[4]


def test_flow_u9_calculate(db_connection):
    """Test the `calculate` flow."""
    expected = int(
        sum(
            [
                u9.u9_for_level(Level.CITY, TIMESPAN, chunk_size=1000)["value"].sum(),
                u9.u9_for_level(Level.EPCI, TIMESPAN, chunk_size=1000)["value"].sum(),
                u9.u9_for_level(Level.DEPARTMENT, TIMESPAN, chunk_size=1000)[
                    "value"
                ].sum(),
                u9.u9_for_level(Level.REGION, TIMESPAN, chunk_size=1000)["value"].sum(),
                u9.u9_national(TIMESPAN)["value"].sum(),
            ]
        )
    )
    all_levels = [
        Level.NATIONAL,
        Level.REGION,
        Level.DEPARTMENT,
        Level.CITY,
        Level.EPCI,
    ]
    indicators = u9.calculate(
        TIMESPAN, all_levels, create_artifact=True, format_pd=True
    )
    assert int(indicators["value"].sum()) == expected


# query used to get N_LEVEL
