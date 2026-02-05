"""Fixtures for pytest."""

import os
from typing import Generator

import pytest
from prefect.testing.utilities import prefect_test_harness
from s3fs import S3FileSystem
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

from indicators.conf import settings
from indicators.db import get_indicators_db_engine
from indicators.schemas import BaseIndicator
from indicators.types import Environment
from tiruert.carbure import CarbureAPISettings, CarbureAPIUser, CarbureClient


@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    """Autouse the prefect test context."""
    with prefect_test_harness(120):
        yield


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """QualiCharge database engine fixture."""
    engine = create_engine(
        str(settings.API_DATABASE_URLS[Environment.TEST]), echo=False
    )
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


@pytest.fixture(scope="function")
def indicators_db_engine() -> Generator[Engine, None, None]:
    """QualiCharge indicators database engine fixture."""
    engine = get_indicators_db_engine()
    yield engine
    # Clean test table
    BaseIndicator.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def indicators_db_connection(indicators_db_engine) -> Generator[Connection, None, None]:
    """Test connection fixture for indicators (uses transaction)."""
    connection = indicators_db_engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def clean_s3fs(request):
    """Yield connected s3fs and remove test.parquet files from S3 bucket.

    NB: the bucket name should be given as a param.
    """
    bucket = request.param
    endpoint_url = os.environ.get("S3_ENDPOINT_URL", None)
    s3 = S3FileSystem(anon=False, endpoint_url=endpoint_url)

    yield s3

    for archive in s3.glob(f"{bucket}/**/test.parquet"):
        s3.rm(archive, recursive=False)


@pytest.fixture(scope="function")
def carbure_api_user():
    """Generate a carbure user."""
    return CarbureAPIUser(
        email="foo@example.org",
        password="supersecret",  # noqa: S106
        api_key="supersecretsecret",
    )


@pytest.fixture(scope="function")
def carbure_config(carbure_api_user):
    """Generate a carbure configuration."""
    return CarbureAPISettings(
        root_url="http://localhost:8088",
        user=carbure_api_user,
    )


@pytest.fixture(scope="function")
def carbure_client(responses, carbure_config):
    """An authenticated carbure API client."""
    client = CarbureClient(carbure_config)

    # Perform initial authentication
    responses.post(
        f"{carbure_config.root_url}api/token/",
        status=200,
        json={
            "access": "access",
            "refresh": "refresh",
        },
    )
    client._auth()

    yield client
