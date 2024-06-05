"""Fixtures for pytest."""

import pytest
from typer.testing import CliRunner

from qcc.client import QCC
from qcc.http import HTTPClient, OAuth2AccessToken


@pytest.fixture
def client():
    """The async HTTP client."""
    client = HTTPClient(
        username="admin",
        password="admin",  # noqa: S106
        base_url="http://example.com/api/v1",
    )
    client._auth = OAuth2AccessToken("fake-token")
    yield client


@pytest.fixture
def qcc():
    """The QualiCharge API client."""
    api_client = QCC(
        username="admin",
        password="admin",  # noqa: S106
        api_root_url="http://example.com/api/v1",
    )
    api_client.client._auth = OAuth2AccessToken("fake-token")
    yield api_client


@pytest.fixture
def runner():
    """CLI runner."""
    yield CliRunner()
