"""QualiCharge API v1 auth router."""

import logging
from typing import Annotated

from fastapi import APIRouter, Security

from qualicharge.auth.models import IDToken, User
from qualicharge.auth.oidc import get_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/whoami")
async def me(token: Annotated[IDToken, Security(get_token)]) -> User:
    """A test endpoint to validate user authentication."""
    logger.debug(f"{token=}")
    return User(email=token.email)
