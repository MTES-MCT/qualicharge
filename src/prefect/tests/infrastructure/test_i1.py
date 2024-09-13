"""QualiCharge prefect indicators tests: infrastructure.

I1: the number of publicly open points of charge.
"""

import pandas as pd
import pytest
from sqlalchemy import text

from indicators.infrastructure import i1
from indicators.models import IndicatorPeriod, Level


def test_task_get_database_engine():
    """Test the `get_database_engine` task."""
    engine = i1.get_database_engine.fn()
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.first()[0] == 1


@pytest.mark.parametrize(
    "level,expected",
    [
        (Level.CITY, 35074),
        (Level.DEPARTMENT, 109),
        (Level.EPCI, 1255),
        (Level.REGION, 26),
    ],
)
def test_task_get_targets_for_level(db_connection, level, expected):
    """Test the `get_targets_for_level` task."""
    assert len(i1.get_targets_for_level.fn(db_connection, level)) == expected


def test_task_get_targets_for_level_unexpected_level(db_connection):
    """Test the `get_targets_for_level` task (unexpected level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        i1.get_targets_for_level.fn(db_connection, Level.NATIONAL)


@pytest.mark.parametrize(
    "level,query,expected",
    [
        (
            Level.CITY,
            "SELECT id FROM City WHERE name IN ('Paris', 'Marseille', 'Lyon')",
            212,
        ),
        (
            Level.EPCI,
            "SELECT id FROM EPCI WHERE code IN ('200054781', '200054807', '200046977')",
            2257,
        ),
        (
            Level.DEPARTMENT,
            "SELECT id FROM Department WHERE code IN ('59', '75', '13')",
            1493,
        ),
        (
            Level.REGION,
            "SELECT id FROM Region WHERE code IN ('11', '84', '75')",
            8734,
        ),
    ],
)
def test_task_get_points_of_charge_for_target(db_connection, level, query, expected):
    """Test the `get_points_of_charge_for_target` task."""
    result = db_connection.execute(text(query))
    indexes = list(result.scalars().all())
    poc = i1.get_points_of_charge_for_targets.fn(db_connection, level, indexes)
    assert len(poc) == len(indexes)
    assert poc["num_poc"].sum() == expected


def test_task_get_points_of_charge_for_target_unexpected_level(db_connection):
    """Test the `get_points_of_charge_for_target` task (unknown level)."""
    with pytest.raises(NotImplementedError, match="Unsupported level"):
        i1.get_points_of_charge_for_targets.fn(db_connection, Level.NATIONAL, [])


@pytest.mark.parametrize(
    "level,query,targets,expected",
    [
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
            2257,
        ),
        (
            Level.DEPARTMENT,
            "SELECT COUNT(*) FROM Department",
            ["59", "75", "13"],
            1493,
        ),
        (
            Level.REGION,
            "SELECT COUNT(*) FROM Region",
            ["11", "84", "75"],
            8734,
        ),
    ],
)
def test_flow_i1_for_level(db_connection, level, query, targets, expected):
    """Test the `i1_for_level` flow."""
    now = pd.Timestamp.now()
    indicators = i1.i1_for_level(level, IndicatorPeriod.DAY, now, chunk_size=1000)
    assert len(indicators) == db_connection.execute(text(query)).scalars().one()
    assert indicators.loc[indicators["target"].isin(targets), "value"].sum() == expected


@pytest.mark.parametrize("chunk_size", [10, 50, 100, 500])
def test_flow_i1_for_level_with_various_chunk_sizes(chunk_size):
    """Test the `i1_for_level` flow with various chunk sizes."""
    now = pd.Timestamp.now()
    indicators = i1.i1_for_level(
        Level.DEPARTMENT, IndicatorPeriod.DAY, now, chunk_size=chunk_size
    )
    n_dpts = 109
    target_pocs = 1493
    assert len(indicators) == n_dpts
    assert (
        indicators.loc[indicators["target"].isin(["59", "75", "13"]), "value"].sum()
        == target_pocs
    )


def test_flow_i1_national(db_connection):
    """Test the `i1_national` flow."""
    result = db_connection.execute(text("SELECT COUNT(id) FROM PointDeCharge"))
    expected = result.scalars().one()
    indicators = i1.i1_national(IndicatorPeriod.DAY, pd.Timestamp.now())
    assert indicators.at[0, "value"] == expected


def test_flow_calculate(db_connection):
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
    indicators = i1.calculate(IndicatorPeriod.DAY, create_artifact=True)
    assert len(indicators) == expected
