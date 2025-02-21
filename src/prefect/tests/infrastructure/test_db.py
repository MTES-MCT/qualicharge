"""QualiCharge prefect indicators tests: databases."""

from sqlalchemy import text

from indicators.db import get_api_db_engine, get_indicators_db_engine
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
