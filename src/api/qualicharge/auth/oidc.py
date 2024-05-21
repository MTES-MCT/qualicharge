"""OpenID Connect authentication."""

import logging
from functools import lru_cache
from typing import Annotated, Dict

import httpx
from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    SecurityScopes,
)
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError
from pydantic import AnyHttpUrl

from ..conf import settings
from ..exceptions import OIDCAuthenticationError, OIDCProviderException
from .models import IDToken

# API auth logger
logger = logging.getLogger(__name__)

oidc_scheme = HTTPBearer()


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
    token: Annotated[HTTPAuthorizationCredentials, Depends(oidc_scheme)],
) -> IDToken:
    """Decode and validate OpenId Connect ID token given a configured provider.

    Args:
        security_scopes (SecurityScopes): additionnal security scopes to check
            (Not Implemented yet)
        token (str): the raw base64-encoded token

    Return:
        id_token (IDToken): Authenticated user ID token.

    Raises:
        OIDCAuthenticationError
    """
    logger.debug(f"{token=}")

    provider_config = discover_provider(settings.OIDC_CONFIGURATION_URL)
    logger.debug(f"{provider_config=}")

    keys = get_public_keys(provider_config["jwks_uri"])
    logger.debug(f"{keys=}")

    try:
        decoded_token = jwt.decode(
            token=token.credentials,
            key=keys,
            algorithms=provider_config["id_token_signing_alg_values_supported"],
            audience=settings.OIDC_EXPECTED_AUDIENCE,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
            },
        )
    except ExpiredSignatureError as exc:
        logger.error("Token signature expired: %s", exc)
        raise OIDCAuthenticationError("Token signature expired") from exc
    except JWTClaimsError as exc:
        logger.error("Bad token claims: %s", exc)
        raise OIDCAuthenticationError("Bad token claims") from exc
    except JWTError as exc:
        logger.error("Unable to decode the ID token: %s", exc)
        raise OIDCAuthenticationError("Unable to decode ID token") from exc
    logger.debug(f"{decoded_token=}")

    return IDToken(**decoded_token)
