"""Tests for the QualiCharge API auth router."""

import datetime

import jwt
import pytest
from fastapi import status

from qualicharge.auth.factories import IDTokenFactory
from qualicharge.auth.models import IDToken, UserCreate, UserRead
from qualicharge.auth.oidc import discover_provider, get_public_keys, get_user_from_db
from qualicharge.auth.schemas import User
from qualicharge.conf import settings
from qualicharge.db import SAQueryCounter


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


@pytest.mark.parametrize(
    "client_auth",
    ((True, {"email": "jane@doe.com", "username": "jdoe"}),),
    indirect=True,
)
def test_whoami_auth_get_user_cache(client_auth, db_session):
    """Test the get_user cache on the whoami endpoint."""
    cache_info = get_user_from_db.cache_info()
    assert cache_info.hits == 0
    assert cache_info.currsize == 0

    with SAQueryCounter(db_session.connection()) as counter:
        response = client_auth.get("/auth/whoami")
    expected = 2
    assert counter.count == expected
    assert response.status_code == status.HTTP_200_OK
    cache_info = get_user_from_db.cache_info()
    assert cache_info.hits == 0
    assert cache_info.currsize == 1

    user = UserRead(**response.json())
    assert user.email == "jane@doe.com"

    # Now we should be using cache 10 times
    for hit in range(1, 10):
        with SAQueryCounter(db_session.connection()) as counter:
            response = client_auth.get("/auth/whoami")
        cache_info = get_user_from_db.cache_info()
        assert counter.count == 0
        assert cache_info.hits == hit
        assert cache_info.currsize == 1
        assert response.status_code == status.HTTP_200_OK
        user = UserRead(**response.json())
        assert user.email == "jane@doe.com"


def test_whoami_expired_signature(
    client, httpx_mock, monkeypatch, id_token_factory=IDTokenFactory
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
    iat = int(datetime.datetime.now().timestamp()) - 500
    token = jwt.encode(
        id_token_factory.build(iat=iat).model_dump(),
        key="secret",
        algorithm="HS256",
    )
    response = client.get("/auth/whoami", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "message": "Authentication failed: Token signature expired"
    }


def test_whoami_with_bad_token_claims(
    client, httpx_mock, monkeypatch, id_token_factory=IDTokenFactory
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
        id_token_factory.build(aud="fake").model_dump(),
        key="secret",
        algorithm="HS256",
    )
    response = client.get("/auth/whoami", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"message": "Authentication failed: Invalid audience"}


def test_whoami_jwt_decoding_error(client, httpx_mock, monkeypatch):
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


def test_login_with_invalid_user(client):
    """Test the login endpoint with invalid user."""
    response = client.post(
        "/auth/token", data={"username": "johndoe", "password": "foo"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "message": "Authentication failed: Wrong login or password"
    }


def test_login_with_invalid_password(client, db_session):
    """Test the login endpoint with invalid password."""
    user = User(
        **UserCreate(
            username="johndoe",
            password="foo",  # noqa: S106
            email="john@doe.com",
            first_name="John",
            last_name="Doe",
            is_superuser=False,
            is_staff=False,
            is_active=True,
        ).model_dump()
    )
    db_session.add(user)

    response = client.post(
        "/auth/token", data={"username": "johndoe", "password": "bar"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "message": "Authentication failed: Wrong login or password"
    }


def test_login_with_inactive_user(client, db_session):
    """Test the login endpoint with an inactive user."""
    user = User(
        **UserCreate(
            username="johndoe",
            password="foo",  # noqa: S106
            email="john@doe.com",
            first_name="John",
            last_name="Doe",
            is_superuser=False,
            is_staff=False,
            is_active=False,
        ).model_dump()
    )
    db_session.add(user)

    response = client.post(
        "/auth/token", data={"username": "johndoe", "password": "foo"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"message": "Authentication failed: User is not active"}


def test_login(client, db_session, monkeypatch):
    """Test the login endpoint."""
    user = User(
        **UserCreate(
            username="johndoe",
            password="foo",  # noqa: S106
            email="john@doe.com",
            first_name="John",
            last_name="Doe",
            is_superuser=False,
            is_staff=False,
            is_active=True,
        ).model_dump(),
        last_login=None,
    )
    db_session.add(user)

    # User never logged in
    assert user.last_login is None

    # Freeze time
    frozen = datetime.datetime.now(datetime.timezone.utc)

    class Freezed(datetime.datetime):
        @classmethod
        def now(cls, *args, **kwargs):
            return frozen

    monkeypatch.setattr(datetime, "datetime", Freezed)

    response = client.post(
        "/auth/token", data={"username": "johndoe", "password": "foo"}
    )
    assert response.status_code == status.HTTP_200_OK
    token = response.json()
    assert token["token_type"] == "bearer"  # noqa: S105
    decoded = jwt.decode(
        token["access_token"],
        key=settings.OAUTH2_TOKEN_ENCODING_KEY,
        algorithms=settings.OAUTH2_TOKEN_ALGORITHMS,
        audience=settings.OIDC_EXPECTED_AUDIENCE,
    )
    id_token = IDToken(**decoded)
    assert id_token.sub == "johndoe"
    assert id_token.email == "john@doe.com"

    # last_login field should have been updated
    db_session.refresh(user)
    assert user.last_login is not None
    assert user.last_login == frozen
