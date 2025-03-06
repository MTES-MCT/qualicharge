"""QualiCharge prefect indicators tests: databases."""

from datetime import datetime

import pytest  # type: ignore
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from indicators.db import (
    create_tables,
    get_api_db_engine,
    get_indicators_db_engine,
    save_indicators,
)
from indicators.infrastructure import i1  # type: ignore
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level
from indicators.types import Environment

TIMESPAN = IndicatorTimeSpan(start=datetime.now(), period=IndicatorPeriod.DAY)


def test_get_api_db_engine():
    """Test the `get_api_db_engine` utility."""
    engine = get_api_db_engine(Environment.TEST)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.first()[0] == 1

    # Test cache
    assert engine == get_api_db_engine(Environment.TEST)


def test_get_indicators_db_engine():
    """Test the `get_indicators_db_engine` utility."""
    engine = get_indicators_db_engine()
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.first()[0] == 1

    # Test singleton
    assert engine == get_indicators_db_engine()


def test_create_tables(indicators_db_engine):
    """Test indicators table creation."""
    with indicators_db_engine.connect() as connection:
        with pytest.raises(ProgrammingError, match='relation "test" does not exist'):
            connection.execute(text("SELECT * FROM test"))

    create_tables()

    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM test"))
        assert result.all() == []


def test_save_indicators(indicators_db_engine):
    """Test save_indicators utility."""
    # Get data sample
    indicators = i1.i1_for_level(
        Level.DEPARTMENT, TIMESPAN, Environment.TEST, chunk_size=1000
    )

    # The test table should not exist yet
    with indicators_db_engine.connect() as connection:
        with pytest.raises(ProgrammingError, match='relation "test" does not exist'):
            connection.execute(text("SELECT * FROM test"))

    save_indicators(Environment.TEST, indicators)

    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test"))
        assert result.one()[0] == len(indicators)

    # Save a second time to ensure we don't mess with tables creation
    save_indicators(Environment.TEST, indicators)
    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test"))
        assert result.one()[0] == 2 * len(indicators)
