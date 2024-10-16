"""Fixtures for pytest."""

from typing import Generator

import pytest
from prefect.testing.utilities import prefect_test_harness
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

from indicators.conf import settings


@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    """Autouse the prefect test context."""
    with prefect_test_harness(60):
        yield


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """QualiCharge database engine fixture."""
    engine = create_engine(str(settings.DATABASE_URL), echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_connection(db_engine) -> Generator[Connection, None, None]:
    """Test connection fixture (uses transaction)."""
    connection = db_engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()
