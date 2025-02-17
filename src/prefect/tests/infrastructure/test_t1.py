"""QualiCharge prefect indicators tests: infrastructure.

T1: the number of publicly open points of charge by power level.
"""

import pandas as pd  # type: ignore
import pytest  # type: ignore
from sqlalchemy import text

from indicators.infrastructure import t1  # type: ignore
from indicators.models import IndicatorPeriod, Level  # type: ignore
from indicators.types import Environment

PARAMETERS_FLOW = [
    (
        Level.CITY,
        "SELECT COUNT(*) FROM City",
        ["75056", "13055", "69123"],
        212,
    ),
    (
        Level.EPCI,
        "SELECT COUNT(*) FROM EPCI",
        ["200054781", "200054807", "200046977"],
        2250,
    ),
    (
        Level.DEPARTMENT,
        "SELECT COUNT(*) FROM Department",
        ["59", "75", "13"],
        1489,
    ),
    (
        Level.REGION,
        "SELECT COUNT(*) FROM Region",
        ["11", "84", "75"],
        8724,
    ),
]
PARAMETERS_GET_VALUES = [
    (
        Level.CITY,
        "SELECT id FROM City WHERE name IN ('Paris', 'Marseille', 'Lyon')",
        212,
    ),
    (
        Level.EPCI,
        "SELECT id FROM EPCI WHERE code IN ('200054781', '200054807', '200046977')",
        2250,
    ),
    (
        Level.DEPARTMENT,
        "SELECT id FROM Department WHERE code IN ('59', '75', '13')",
        1489,
    ),
    (
        Level.REGION,
        "SELECT id FROM Region WHERE code IN ('11', '84', '75')",
        8724,
    ),
]
PARAMETERS_CHUNK = [10, 50, 100, 500]
PERIOD = IndicatorPeriod.DAY


@pytest.mark.parametrize("level,query,expected", PARAMETERS_GET_VALUES)
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
    now = pd.Timestamp.now()
    indicators = t1.t1_for_level(level, PERIOD, now, Environment.TEST, chunk_size=1000)
    # assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


@pytest.mark.parametrize("chunk_size", PARAMETERS_CHUNK)
def test_flow_t1_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `t1_for_level` flow with various chunk sizes."""
    level, query, targets, expected = PARAMETERS_FLOW[2]
    now = pd.Timestamp.now()
    indicators = t1.t1_for_level(
        level, PERIOD, now, Environment.TEST, chunk_size=chunk_size
    )
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


def test_flow_t1_national(db_connection):
    """Test the `t1_national` flow."""
    query = "SELECT COUNT(*) FROM PointDeCharge WHERE puissance_nominale::numeric >= 0"
    expected = db_connection.execute(text(query)).scalars().one()
    indicators = t1.t1_national(PERIOD, pd.Timestamp.now(), Environment.TEST)
    assert indicators["value"].sum() == expected


def test_flow_calculate():
    """Test the `calculate` flow."""
    now = pd.Timestamp.now()
    expected = sum(
        [
            t1.t1_for_level(Level.CITY, PERIOD, now, Environment.TEST, chunk_size=1000)[
                "value"
            ].sum(),
            t1.t1_for_level(Level.EPCI, PERIOD, now, Environment.TEST, chunk_size=1000)[
                "value"
            ].sum(),
            t1.t1_for_level(
                Level.DEPARTMENT, PERIOD, now, Environment.TEST, chunk_size=1000
            )["value"].sum(),
            t1.t1_for_level(
                Level.REGION, PERIOD, now, Environment.TEST, chunk_size=1000
            )["value"].sum(),
            t1.t1_national(PERIOD, now, Environment.TEST)["value"].sum(),
        ]
    )
    indicators = t1.calculate(PERIOD, Environment.TEST, create_artifact=True)
    pd_indics = pd.DataFrame.from_records([indic.model_dump() for indic in indicators])
    assert pd_indics["value"].sum() == expected


def test_flow_calculate_persistence(indicators_db_engine):
    """Test the `calculate` flow."""
    indicators = t1.calculate(PERIOD, Environment.TEST, persist=True)

    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test WHERE code = 't1'"))
        assert result.one()[0] == len(indicators)
