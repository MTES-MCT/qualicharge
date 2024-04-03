"""App HTTP client pytest fixtures."""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from qualicharge.api.v1 import app
from qualicharge.auth.models import IDToken
from qualicharge.auth.oidc import get_token
from qualicharge.conf import settings


@pytest.fixture
def id_token_factory() -> IDToken:
    """Generate a fake IDToken."""
    now = datetime.now().timestamp()
    return IDToken(
        iss=str(settings.OIDC_PROVIDER_BASE_URL),
        sub=str(uuid.uuid4()),
        aud=settings.OIDC_EXPECTED_AUDIENCE,
        exp=int(now) + 300,
        iat=int(now),
        scope="email profile",
        email="john@doe.com",
    )


@pytest.fixture
def client():
    """A test client configured for the /api/v1 application."""
    yield TestClient(app)


@pytest.fixture
def client_auth(id_token_factory):
    """An authenticated test client configured for the /api/v1 application."""
    app.dependency_overrides[get_token] = lambda: id_token_factory
    yield TestClient(app)
    app.dependency_overrides = {}
