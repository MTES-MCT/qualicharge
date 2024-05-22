"""Tests for the QualiCharge API auth router."""

from datetime import datetime

import pytest
from fastapi import status
from jose import jwt

from qualicharge.auth.factories import IDTokenFactory
from qualicharge.auth.models import UserRead
from qualicharge.auth.oidc import discover_provider, get_public_keys
from qualicharge.conf import settings


def setup_function():
    """Inactivate auth-specific LRU cache."""
    discover_provider.cache_clear()
    get_public_keys.cache_clear()


def test_whoami_not_auth(client):
    """Test the whoami endpoint when user is not authenticated."""
    response = client.get("/auth/whoami")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("client_auth", ((False, {}),), indirect=True)
def test_whoami_auth_not_registered_user(client_auth):
    """Test the whoami endpoint when user is authenticated but not registered."""
    response = client_auth.get("/auth/whoami")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "message": "Authentication failed: User is not registered yet"
    }


@pytest.mark.parametrize(
    "client_auth", ((True, {"email": "jane@doe.com"}),), indirect=True
)
def test_whoami_auth(client_auth):
    """Test the whoami endpoint when user is authenticated."""
    response = client_auth.get("/auth/whoami")
    assert response.status_code == status.HTTP_200_OK

    user = UserRead(**response.json())
    assert user.email == "jane@doe.com"
    assert user.is_active is True
    assert user.is_superuser is True
    assert user.is_staff is True


def test_whoami_expired_signature(
    client, id_token_factory: IDTokenFactory, httpx_mock, monkeypatch
):
    """Test the whoami endpoint when user's token expired."""
    monkeypatch.setenv("QUALICHARGE_OIDC_PROVIDER_BASE_URL", "http://oidc")
    httpx_mock.add_response(
        method="GET",
        url=str(settings.OIDC_CONFIGURATION_URL),
        json={
            "jwks_uri": "https://oidc/certs",
            "id_token_signing_alg_values_supported": "HS256",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="https://oidc/certs",
        json=[
            "secret",
        ],
    )
    # As exp should be set to iat + 300, the token should be expired
    iat = int(datetime.now().timestamp()) - 500
    token = jwt.encode(
        claims=id_token_factory.build(iat=iat).model_dump(),
        key="secret",
        algorithm="HS256",
    )
    response = client.get("/auth/whoami", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "message": "Authentication failed: Token signature expired"
    }


def test_whoami_with_bad_token_claims(
    client, id_token_factory: IDTokenFactory, httpx_mock, monkeypatch
):
    """Test the whoami endpoint with bad token claims."""
    monkeypatch.setenv("QUALICHARGE_OIDC_PROVIDER_BASE_URL", "http://oidc")
    httpx_mock.add_response(
        method="GET",
        url=str(settings.OIDC_CONFIGURATION_URL),
        json={
            "jwks_uri": "https://oidc/certs",
            "id_token_signing_alg_values_supported": "HS256",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="https://oidc/certs",
        json=[
            "secret",
        ],
    )
    # As exp should be set to iat + 300, the token should be expired
    token = jwt.encode(
        claims=id_token_factory.build(aud="fake").model_dump(),
        key="secret",
        algorithm="HS256",
    )
    response = client.get("/auth/whoami", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"message": "Authentication failed: Bad token claims"}


def test_whoami_jwt_decoding_error(
    client, id_token_factory: IDTokenFactory, httpx_mock, monkeypatch
):
    """Test the whoami endpoint when JWT decoding fails."""
    monkeypatch.setenv("QUALICHARGE_OIDC_PROVIDER_BASE_URL", "http://oidc")
    httpx_mock.add_response(
        method="GET",
        url=str(settings.OIDC_CONFIGURATION_URL),
        json={
            "jwks_uri": "https://oidc/certs",
            "id_token_signing_alg_values_supported": "HS256",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="https://oidc/certs",
        json=[
            "secret",
        ],
    )
    token = "faketoken"  # noqa: S105
    response = client.get("/auth/whoami", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "message": "Authentication failed: Unable to decode ID token"
    }
