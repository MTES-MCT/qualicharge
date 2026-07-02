"""QualiCharge prefect indicators tests: extract.

E1: the list of stations in activity per pool.
"""

from datetime import datetime

from sqlalchemy import text

from indicators.extract import e1, e5
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level
from indicators.types import Environment

# expected result
N_POOLS_STATIONS = 363

TIMESPAN = IndicatorTimeSpan(start=datetime(2025, 1, 1), period=IndicatorPeriod.DAY)


def test_get_pdc_station_for_day():
    """Test the `get_pdc_station_for_day` function."""
    e5.e5(
        Environment.TEST,
        [Level.NATIONAL],
        start=TIMESPAN.start + TIMESPAN.period.duration,
        period=TIMESPAN.period.value,
        persist=True,
    )
    poc_station = e1.get_pdc_station_for_day(TIMESPAN.start.date(), Environment.TEST)
    assert not poc_station.empty
    assert set(poc_station.columns) == {
        "latitude",
        "longitude",
        "puissance_nominale",
        "id_pdc_itinerance",
        "id_station_itinerance",
    }


def test_get_station_pool_for_day():
    """Test the `get_station_pool_for_day` function."""
    e5.e5(
        Environment.TEST,
        [Level.NATIONAL],
        start=TIMESPAN.start + TIMESPAN.period.duration,
        period=TIMESPAN.period.value,
        persist=True,
    )
    pool_station = e1.get_station_pool_for_day(TIMESPAN.start.date(), Environment.TEST)
    assert not pool_station.empty
    assert set(pool_station.columns) == {
        "id_pool",
        "id_station_itinerance",
    }
    assert len(pool_station) == N_POOLS_STATIONS


def test_flow_e1():
    """Test the `e1` flow."""
    e5.e5(
        Environment.TEST,
        [Level.NATIONAL],
        start=TIMESPAN.start,
        period=TIMESPAN.period.value,
        persist=True,
    )

    indicators = e1.e1(
        Environment.TEST,
        start=TIMESPAN.start,
        create_artifact=False,
    )
    assert list(indicators["level"].unique()) == [0]


def test_flow_e1_persistence(indicators_db_engine):
    """Test the `e1` flow."""
    e5.e5(
        Environment.TEST,
        [Level.NATIONAL],
        start=TIMESPAN.start,
        period=TIMESPAN.period.value,
        persist=True,
    )
    indicators = e1.e1(
        Environment.TEST, start=TIMESPAN.start, create_artifact=False, persist=True
    )
    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test WHERE code = 'e1'"))
        assert result.one()[0] == len(indicators)
