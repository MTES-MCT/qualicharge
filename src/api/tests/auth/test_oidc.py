"""Tests for qualicharge.auth.oidc module."""

from datetime import datetime
from typing import Union

import httpx
import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials, SecurityScopes
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, IDTokenFactory, UserFactory
from qualicharge.auth.oidc import (
    discover_provider,
    get_public_keys,
    get_token,
    get_user,
    get_user_from_db,
)
from qualicharge.auth.schemas import GroupOperationalUnit, ScopesEnum
from qualicharge.conf import settings
from qualicharge.db import SAQueryCounter
from qualicharge.exceptions import (
    AuthenticationError,
    OIDCProviderException,
    PermissionDenied,
)
from qualicharge.schemas.core import OperationalUnit


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


@pytest.mark.parametrize("oidc_is_enabled", (True, False))
def test_get_token(
    oidc_is_enabled,
    httpx_mock,
    monkeypatch,
    id_token_factory: IDTokenFactory = IDTokenFactory,
):
    """Test the OIDC get token utility."""
    monkeypatch.setenv("QUALICHARGE_OIDC_PROVIDER_BASE_URL", "http://oidc")
    monkeypatch.setattr(settings, "OIDC_IS_ENABLED", oidc_is_enabled)
    monkeypatch.setattr(settings, "OAUTH2_TOKEN_ENCODING_KEY", "secret")

    if oidc_is_enabled:
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

    token = jwt.encode(
        id_token_factory.build().model_dump(),
        key="secret",
    )
    bearer_token: Union[str, HTTPAuthorizationCredentials] = token
    if oidc_is_enabled:
        bearer_token = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

    id_token = get_token(security_scopes=SecurityScopes(), token=bearer_token)
    assert id_token.email == "john@doe.com"


@pytest.mark.parametrize("oidc_is_enabled", (True, False))
def test_get_token_with_expired_token(
    oidc_is_enabled,
    httpx_mock,
    monkeypatch,
    id_token_factory: IDTokenFactory = IDTokenFactory,
):
    """Test the OIDC get token utility when the token expired."""
    monkeypatch.setenv("QUALICHARGE_OIDC_PROVIDER_BASE_URL", "http://oidc")
    monkeypatch.setattr(settings, "OIDC_IS_ENABLED", oidc_is_enabled)
    monkeypatch.setattr(settings, "OAUTH2_TOKEN_ENCODING_KEY", "secret")

    if oidc_is_enabled:
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
        id_token_factory.build(iat=iat).model_dump(),
        key="secret",
    )
    bearer_token: Union[str, HTTPAuthorizationCredentials] = token
    if oidc_is_enabled:
        bearer_token = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

    with pytest.raises(AuthenticationError, match="Token signature expired"):
        get_token(security_scopes=SecurityScopes(), token=bearer_token)


def test_get_user_with_not_registered_user(
    db_session, id_token_factory: IDTokenFactory = IDTokenFactory
):
    """Test the OIDC get user utility when user is not registered."""
    with pytest.raises(AuthenticationError, match="User is not registered yet"):
        get_user(
            security_scopes=SecurityScopes(),
            token=id_token_factory.build(),
            session=db_session,
        )


def test_get_user_with_not_active_user(
    db_session, id_token_factory: IDTokenFactory = IDTokenFactory
):
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


def test_get_user_for_admin_user(
    db_session, id_token_factory: IDTokenFactory = IDTokenFactory
):
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
    db_session, id_token_factory: IDTokenFactory = IDTokenFactory
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


def test_get_user_number_of_queries(
    db_session, id_token_factory: IDTokenFactory = IDTokenFactory
):
    """Test the OIDC get user utility number of queries for a standard user."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    token = id_token_factory.build()

    # Create groups linked to Operational Units
    groups = GroupFactory.create_batch_sync(3)
    operational_units = db_session.exec(select(OperationalUnit).limit(3)).all()
    for group, operational_unit in zip(groups, operational_units, strict=True):
        db_session.add(
            GroupOperationalUnit(
                group_id=group.id, operational_unit_id=operational_unit.id
            )
        )

    # Create user linked to this groups and related operational units
    user = UserFactory.create_sync(
        email=token.email,
        is_superuser=False,
        is_active=True,
        groups=groups,
        scopes=[ScopesEnum.ALL_CREATE],
    )

    # Test the number of queries
    with SAQueryCounter(db_session.connection()) as counter:
        user = get_user(
            security_scopes=SecurityScopes(scopes=[ScopesEnum.ALL_CREATE]),
            token=token,
            session=db_session,
        )
    assert counter.count == 1

    # When getting groups...
    with SAQueryCounter(db_session.connection()) as counter:
        assert {g.id for g in user.groups} == {g.id for g in groups}
    assert counter.count == 0

    # ... and related operational units
    with SAQueryCounter(db_session.connection()) as counter:
        assert {ou.id for g in user.groups for ou in g.operational_units} == {
            ou.id for ou in operational_units
        }
    assert counter.count == 0


def test_get_user_cache(db_session, id_token_factory: IDTokenFactory = IDTokenFactory):
    """Test the OIDC get user utility number of queries for a standard user."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    token = id_token_factory.build()

    # Create groups linked to Operational Units
    groups = GroupFactory.create_batch_sync(3)
    operational_units = db_session.exec(select(OperationalUnit).limit(3)).all()
    for group, operational_unit in zip(groups, operational_units, strict=True):
        db_session.add(
            GroupOperationalUnit(
                group_id=group.id, operational_unit_id=operational_unit.id
            )
        )

    # Create user linked to this groups and related operational units
    user = UserFactory.create_sync(
        email=token.email,
        is_superuser=False,
        is_active=True,
        groups=groups,
        scopes=[ScopesEnum.ALL_CREATE],
    )
    security_scopes = SecurityScopes(scopes=[ScopesEnum.ALL_CREATE])

    # Test the original number of queries
    with SAQueryCounter(db_session.connection()) as counter:
        user = get_user(
            security_scopes=security_scopes,
            token=token,
            session=db_session,
        )
    cache_info = get_user_from_db.cache_info()  # type: ignore[attr-defined]
    assert counter.count == 1
    assert cache_info.hits == 0
    assert cache_info.currsize == 1

    # User should be cached, we should not hit the database
    for hit in range(1, 10):
        with SAQueryCounter(db_session.connection()) as counter:
            user = get_user(
                security_scopes=security_scopes,
                token=token,
                session=db_session,
            )
        cache_info = get_user_from_db.cache_info()  # type: ignore[attr-defined]
        assert counter.count == 0
        assert cache_info.hits == hit
        assert cache_info.currsize == 1

    # When getting groups...
    with SAQueryCounter(db_session.connection()) as counter:
        assert {g.id for g in user.groups} == {g.id for g in groups}
    assert counter.count == 0

    # ... and related operational units
    with SAQueryCounter(db_session.connection()) as counter:
        assert {ou.id for g in user.groups for ou in g.operational_units} == {
            ou.id for ou in operational_units
        }
    assert counter.count == 0
