"""QualiCharge API v1."""

import logging
from typing import Annotated

from fastapi import FastAPI, Security

from qualicharge.auth.models import IDToken, User
from qualicharge.auth.oidc import get_token

logger = logging.getLogger(__name__)

app = FastAPI(title="QualiCharge API (v1)")


@app.get("/whoami")
async def me(token: Annotated[IDToken, Security(get_token)]) -> User:
    """A test endpoint to validate user authentication."""
    logger.debug(f"{token=}")
    return User(email=token.email)
