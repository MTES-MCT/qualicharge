"""QualiCharge prefect indicators tests: databases."""

from enum import StrEnum
import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from indicators.conf import settings
from indicators.db import (
    create_tables,
    get_api_db_engine,
    get_indicators_db_engine,
    save_indicators,
)
from indicators.types import Environment


def test_get_api_db_engine():
    """Test the `get_api_db_engine` utility."""
    engine = get_api_db_engine(Environment.DEVELOPMENT)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.first()[0] == 1

    # Test cache
    assert engine == get_api_db_engine(Environment.DEVELOPMENT)


def test_get_indicators_db_engine():
    """Test the `get_indicators_db_engine` utility."""
    engine = get_indicators_db_engine()
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.first()[0] == 1

    # Test singleton
    assert engine == get_indicators_db_engine()


def test_create_tables(indicators_db_engine, monkeypatch):
    """Test indicators table creation."""

    class Environment(StrEnum):
        FAKE = "fake"

    with indicators_db_engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS fake"))

        monkeypatch.setattr(settings, "API_ACTIVE_ENVIRONMENTS", [Environment.FAKE])
        with pytest.raises(ProgrammingError, match='relation "fake" does not exist'):
            connection.execute(text("SELECT * FROM fake"))

    create_tables()

    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM fake"))
        assert result.all() == []

        # Cleanup
        connection.execute(text("DROP TABLE fake"))
