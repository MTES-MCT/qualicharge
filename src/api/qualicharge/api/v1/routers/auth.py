"""QualiCharge API v1 auth router."""

import logging
from typing import Annotated

from fastapi import APIRouter, Security

from qualicharge.auth.models import UserRead
from qualicharge.auth.oidc import get_user
from qualicharge.auth.schemas import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/whoami")
async def me(user: Annotated[User, Security(get_user)]) -> UserRead:
    """A test endpoint to validate user authentication."""
    logger.debug(f"{user=}")
    return UserRead(**user.model_dump())
