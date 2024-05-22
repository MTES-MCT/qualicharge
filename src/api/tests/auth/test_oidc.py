"""Tests for qualicharge.auth.oidc module."""

from datetime import datetime

import httpx
import pytest
from fastapi.security import HTTPAuthorizationCredentials, SecurityScopes
from jose import jwt

from qualicharge.auth.factories import IDTokenFactory, UserFactory
from qualicharge.auth.oidc import (
    discover_provider,
    get_public_keys,
    get_token,
    get_user,
)
from qualicharge.auth.schemas import ScopesEnum
from qualicharge.conf import settings
from qualicharge.exceptions import (
    AuthenticationError,
    OIDCAuthenticationError,
    OIDCProviderException,
    PermissionDenied,
)


def setup_function():
    """Inactivate auth-specific LRU cache."""
    discover_provider.cache_clear()
    get_public_keys.cache_clear()


def test_discover_provider(httpx_mock):
    """Test the OIDC discover provider utility."""
    httpx_mock.add_response(
        method="GET",
        url="http://oidc/config",
        json={"jwks_uri": "https://oidc/certs"},
    )

    assert discover_provider("http://oidc/config") == {"jwks_uri": "https://oidc/certs"}


def test_discover_provider_with_bad_configuration(httpx_mock):
    """Test the OIDC discover provider utility with a bad configuration."""
    httpx_mock.add_exception(httpx.RequestError("Not found!"))

    with pytest.raises(
        OIDCProviderException,
        match="Unable to discover the OIDC provider configuration",
    ):
        discover_provider("http://oidc/wrong")


def test_discover_provider_with_unknown_realm(httpx_mock):
    """Test the OIDC discover provider utility with a unknown realm."""
    httpx_mock.add_response(status_code=404)

    with pytest.raises(
        OIDCProviderException,
        match="Unable to discover the OIDC provider configuration",
    ):
        discover_provider("http://oidc/wrong")


def test_get_public_keys(httpx_mock):
    """Test the OIDC get public keys utility."""
    httpx_mock.add_response(
        method="GET",
        url="http://oidc/certs",
        json=[{"kid": "1"}, {"kid": "2"}],
    )

    assert get_public_keys("http://oidc/certs") == [{"kid": "1"}, {"kid": "2"}]


def test_get_public_keys_with_bad_configuration(httpx_mock):
    """Test the OIDC get public keys utility with a bad configuration."""
    httpx_mock.add_exception(httpx.RequestError("Not found!"))

    with pytest.raises(
        OIDCProviderException,
        match="Unable to retrieve OIDC server signing public keys",
    ):
        get_public_keys("http://oidc/wrong")

    httpx_mock.add_response(status_code=404)
    with pytest.raises(
        OIDCProviderException,
        match="Unable to retrieve OIDC server signing public keys",
    ):
        get_public_keys("http://oidc/wrong")


def test_get_token(httpx_mock, monkeypatch, id_token_factory: IDTokenFactory):
    """Test the OIDC get token utility."""
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

    bearer_token = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=jwt.encode(
            claims=id_token_factory.build().model_dump(), key="secret"
        ),
    )
    token = get_token(security_scopes=SecurityScopes(), token=bearer_token)
    assert token.email == "john@doe.com"


def test_get_token_with_expired_token(
    httpx_mock, monkeypatch, id_token_factory: IDTokenFactory
):
    """Test the OIDC get token utility when the token expired."""
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
    bearer_token = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=jwt.encode(
            claims=id_token_factory.build(iat=iat).model_dump(),
            key="secret",
        ),
    )
    with pytest.raises(OIDCAuthenticationError, match="Token signature expired"):
        get_token(security_scopes=SecurityScopes(), token=bearer_token)


def test_get_user_with_not_registered_user(
    id_token_factory: IDTokenFactory, db_session
):
    """Test the OIDC get user utility when user is not registered."""
    with pytest.raises(AuthenticationError, match="User is not registered yet"):
        get_user(
            security_scopes=SecurityScopes(),
            token=id_token_factory.build(),
            session=db_session,
        )


def test_get_user_with_not_active_user(id_token_factory: IDTokenFactory, db_session):
    """Test the OIDC get user utility when user is not active."""
    UserFactory.__session__ = db_session

    token = id_token_factory.build()
    UserFactory.create_sync(
        email=token.email, is_superuser=False, is_staff=False, is_active=False
    )
    with pytest.raises(AuthenticationError, match="User is not active"):
        get_user(
            security_scopes=SecurityScopes(),
            token=id_token_factory.build(),
            session=db_session,
        )


def test_get_user_for_admin_user(id_token_factory: IDTokenFactory, db_session):
    """Test the OIDC get user utility for an admin user."""
    UserFactory.__session__ = db_session

    token = id_token_factory.build()
    db_user = UserFactory.create_sync(
        email=token.email, is_superuser=True, is_active=True
    )

    # Test with no particular scopes
    user = get_user(
        security_scopes=SecurityScopes(),
        token=token,
        session=db_session,
    )
    assert user == db_user

    # Test with all scopes required
    user = get_user(
        security_scopes=SecurityScopes(scopes=list(ScopesEnum)),
        token=token,
        session=db_session,
    )
    assert user == db_user


def test_get_user_for_user_with_limited_scopes(
    id_token_factory: IDTokenFactory, db_session
):
    """Test the OIDC get user utility for an admin user."""
    UserFactory.__session__ = db_session

    token = id_token_factory.build()
    db_user = UserFactory.create_sync(
        email=token.email,
        is_superuser=False,
        is_active=True,
        scopes=[ScopesEnum.STATIC_READ, ScopesEnum.DYNAMIC_READ],
    )

    # Test with no particular scopes
    user = get_user(
        security_scopes=SecurityScopes(),
        token=token,
        session=db_session,
    )
    assert user == db_user

    # Test with matching user scopes
    user = get_user(
        security_scopes=SecurityScopes(scopes=[ScopesEnum.STATIC_READ]),
        token=token,
        session=db_session,
    )
    assert user == db_user
    user = get_user(
        security_scopes=SecurityScopes(scopes=[ScopesEnum.DYNAMIC_READ]),
        token=token,
        session=db_session,
    )
    assert user == db_user
    user = get_user(
        security_scopes=SecurityScopes(
            scopes=[ScopesEnum.DYNAMIC_READ, ScopesEnum.STATIC_READ]
        ),
        token=token,
        session=db_session,
    )
    assert user == db_user

    # Test with missing required scopes
    with pytest.raises(
        PermissionDenied, match="You are not allowed to access this ressource"
    ):
        get_user(
            security_scopes=SecurityScopes(
                scopes=[
                    ScopesEnum.DYNAMIC_READ,
                    ScopesEnum.STATIC_READ,
                    ScopesEnum.STATIC_CREATE,
                ]
            ),
            token=id_token_factory.build(),
            session=db_session,
        )

    with pytest.raises(
        PermissionDenied, match="You are not allowed to access this ressource"
    ):
        get_user(
            security_scopes=SecurityScopes(scopes=[ScopesEnum.STATIC_CREATE]),
            token=id_token_factory.build(),
            session=db_session,
        )
