"""App HTTP client pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from qualicharge.api.v1 import app
from qualicharge.auth.factories import IDTokenFactory
from qualicharge.auth.oidc import get_token


@pytest.fixture
def client():
    """A test client configured for the /api/v1 application."""
    yield TestClient(app)


@pytest.fixture
def client_auth(id_token_factory: IDTokenFactory):
    """An authenticated test client configured for the /api/v1 application."""
    app.dependency_overrides[get_token] = lambda: id_token_factory.build()
    yield TestClient(app)
    app.dependency_overrides = {}
