"""QualiCharge API v1."""

import logging
from typing import Annotated, Union

from fastapi import FastAPI, Request, Security, status
from fastapi.responses import JSONResponse

from qualicharge.auth.models import IDToken, User
from qualicharge.auth.oidc import get_token
from qualicharge.exceptions import OIDCAuthenticationError, OIDCProviderException

logger = logging.getLogger(__name__)

app = FastAPI(title="QualiCharge API (v1)")


@app.exception_handler(OIDCAuthenticationError)
@app.exception_handler(OIDCProviderException)
async def authentication_exception_handler(
    request: Request, exc: Union[OIDCAuthenticationError, OIDCProviderException]
):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"message": f"Authentication failed: {exc.name}"},
    )


@app.get("/whoami")
async def me(token: Annotated[IDToken, Security(get_token)]) -> User:
    """A test endpoint to validate user authentication."""
    logger.debug(f"{token=}")
    return User(email=token.email)
