"""QualiCharge API v1 auth router."""

import datetime
import logging
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Security
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session as SMSession
from sqlmodel import select

from qualicharge.auth.models import IDToken, Token, UserRead
from qualicharge.auth.oidc import get_user
from qualicharge.auth.schemas import User
from qualicharge.conf import settings
from qualicharge.db import get_async_session
from qualicharge.exceptions import AuthenticationError

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


@router.post("/token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[
        SMSession,
        Depends(get_async_session),
    ],
) -> Token:
    """Log user in by forging an oauth2 jwt token."""
    # Get registered user
    user = (
        await session.exec(select(User).where(User.username == form_data.username))
    ).one_or_none()

    # User does not exist: raise an error
    if user is None:
        logger.error(
            f"User {form_data.username} tried to login but is not registered yet"
        )
        raise AuthenticationError("Wrong login or password")

    # Check password
    if not user.check_password(form_data.password):
        logger.error(f"User {form_data.username} tried to login with a wrong password")
        raise AuthenticationError("Wrong login or password")

    # User is not active: raise an error
    if not user.is_active:
        logger.error(f"User {form_data.username} tried to login but is not active")
        raise AuthenticationError("User is not active")

    # Update user last login field
    now: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    now_timestamp: int = int(now.timestamp())
    user.last_login = now
    session.add(user)
    await session.commit()

    # Forge Token
    id_token = IDToken(
        iss=str(settings.OAUTH2_TOKEN_ISSUER),
        sub=await user.awaitable_attrs.username,
        exp=now_timestamp + settings.OAUTH2_TOKEN_LIFETIME,
        iat=now_timestamp,
        email=await user.awaitable_attrs.email,
        aud=settings.OIDC_EXPECTED_AUDIENCE,
        scope="",
    )
    return Token(
        access_token=jwt.encode(
            id_token.model_dump(),
            settings.OAUTH2_TOKEN_ENCODING_KEY,
            algorithm=settings.OAUTH2_TOKEN_ALGORITHMS[0],
        ),
        token_type="bearer",  # noqa: S106
    )
