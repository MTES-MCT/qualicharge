"""OpenID Connect authentication."""

import logging
from functools import lru_cache
from threading import Lock
from typing import Annotated, Dict, Union

import httpx
import jwt
from cachetools import TTLCache, cached
from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
    SecurityScopes,
)
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidTokenError,
)
from pydantic import AnyHttpUrl
from sentry_sdk import set_user
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..conf import settings
from ..db import get_session, get_async_session
from ..exceptions import (
    AuthenticationError,
    OIDCProviderException,
    PermissionDenied,
)
from .models import IDToken
from .schemas import Group, User

# API auth logger
logger = logging.getLogger(__name__)

auth_scheme: Union[OAuth2PasswordBearer, HTTPBearer] = OAuth2PasswordBearer(
    tokenUrl=settings.OAUTH2_TOKEN_URL
)
if settings.OIDC_IS_ENABLED:
    auth_scheme = HTTPBearer()


@lru_cache()
def discover_provider(
    configuration_url: AnyHttpUrl,
    timeout: int = settings.OIDC_PROVIDER_DISCOVER_TIMEOUT,
) -> Dict:
    """Discover the OpenId Provider configuration."""
    logger.debug("Discovering provider using configuration URL: %s", configuration_url)
    try:
        response = httpx.get(str(configuration_url), timeout=timeout)
        response.raise_for_status()
        logger.debug("Got response: %d -> %s", response.status_code, response.json())
        return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as exc:
        logger.error("Unable to discover the OIDC provider configuration: %s", exc)
        raise OIDCProviderException(
            "Unable to discover the OIDC provider configuration"
        ) from exc


@lru_cache()
def get_public_keys(
    jwks_uri: AnyHttpUrl,
    timeout: int = settings.OIDC_PROVIDER_DISCOVER_TIMEOUT,
) -> Dict:
    """Retrieve the public keys used by the provider server for signing."""
    try:
        response = httpx.get(str(jwks_uri), timeout=timeout)
        response.raise_for_status()
        return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as exc:
        logger.error(
            (
                "Unable to retrieve the public keys used by the provider server"
                "for signing: %s"
            ),
            exc,
        )
        raise OIDCProviderException(
            "Unable to retrieve OIDC server signing public keys"
        ) from exc


def get_token(
    security_scopes: SecurityScopes,
    token: Annotated[Union[HTTPAuthorizationCredentials, str], Depends(auth_scheme)],
) -> IDToken:
    """Decode and validate OpenId Connect ID token given a configured provider.

    Args:
        security_scopes (SecurityScopes): additionnal security scopes to check
            (Not Implemented yet)
        token (str): the raw base64-encoded token

    Return:
        id_token (IDToken): Authenticated user ID token.

    Raises:
        AuthenticationError
    """
    logger.debug(f"{token=}")

    key: Union[str, dict] = settings.OAUTH2_TOKEN_ENCODING_KEY
    algorithms = settings.OAUTH2_TOKEN_ALGORITHMS
    extra_decode_options = {
        "audience": settings.OIDC_EXPECTED_AUDIENCE,
        "options": {
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": True,
        },
    }

    if settings.OIDC_IS_ENABLED:
        provider_config = discover_provider(settings.OIDC_CONFIGURATION_URL)
        logger.debug(f"{provider_config=}")

        algorithms = provider_config["id_token_signing_alg_values_supported"]
        key = get_public_keys(provider_config["jwks_uri"])[0]

    logger.debug(f"{key=}")
    logger.debug(f"{algorithms=}")
    logger.debug(f"{extra_decode_options=}")

    try:
        decoded_token = jwt.decode(
            token.credentials if settings.OIDC_IS_ENABLED else token,  # type: ignore[union-attr, arg-type]
            key=key,
            algorithms=algorithms,
            **extra_decode_options,  # type: ignore[arg-type]
        )
    except ExpiredSignatureError as exc:
        logger.error("Token signature expired: %s", exc)
        raise AuthenticationError("Token signature expired") from exc
    except InvalidAudienceError as exc:
        logger.error("Invalid audience: %s", exc)
        raise AuthenticationError("Invalid audience") from exc
    except InvalidTokenError as exc:
        logger.error("Unable to decode the ID token: %s", exc)
        raise AuthenticationError("Unable to decode ID token") from exc
    logger.debug(f"{decoded_token=}")

    return IDToken(**decoded_token)


@cached(
    TTLCache(
        maxsize=settings.API_GET_USER_CACHE_MAXSIZE,
        ttl=settings.API_GET_USER_CACHE_TTL,
    ),
    lock=Lock(),
    key=lambda email, session: email,
    info=settings.API_GET_USER_CACHE_INFO,
)
async def get_user_from_db(
    email: str,
    session: Annotated[
        AsyncSession,
        Depends(get_async_session),
    ],
) -> User:
    """Fetch user and related objects from database."""
    logging.debug(f"Getting user from database: {email}")
    return (
        (
            await session.exec(
                select(User)
                .options(joinedload(User.groups).joinedload(Group.operational_units))  # type: ignore[arg-type]
                .where(User.email == email)
            )
        )
        .unique()
        .one_or_none()
    )


async def get_user(
    security_scopes: SecurityScopes,
    token: Annotated[IDToken, Depends(get_token)],
    session: Annotated[
        AsyncSession,
        Depends(get_async_session),
    ],
) -> User:
    """Get request user."""
    user = await get_user_from_db(email=token.email, session=session)

    # User does not exist: raise an error
    if user is None:
        logger.error(f"User {token.email} tried to login but is not registered yet")
        raise AuthenticationError("User is not registered yet")

    # User is not active: raise an error
    if not user.is_active:
        logger.error(f"User {token.email} tried to login but is not active")
        raise AuthenticationError("User is not active")

    # Add username to sentry's context
    set_user({"username": user.username})

    # We do not check scopes for admin users
    if user.is_superuser:
        return user

    # Get user scopes from Token scope and database
    user_scopes = set(token.scope.split() if token.scope else []) | set(user.scopes)

    # Validate scopes
    for required_scope in security_scopes.scopes:
        if required_scope not in user_scopes:
            raise PermissionDenied("You are not allowed to access this ressource")

    return user
