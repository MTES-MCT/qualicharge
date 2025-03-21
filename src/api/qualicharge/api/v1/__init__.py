"""QualiCharge API v1."""

import logging
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from qualicharge.conf import settings
from qualicharge.exceptions import (
    AuthenticationError,
    OIDCProviderException,
    PermissionDenied,
)

from .routers import auth, dynamic, manage, static

logger = logging.getLogger(__name__)

app = FastAPI(title="QualiCharge API (v1)", debug=settings.DEBUG)


@app.exception_handler(PermissionDenied)
async def authorization_exception_handler(
    request: Request,
    exc: PermissionDenied,
):
    """Handle authorization errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"message": f"Unsufficient permissions: {exc.name}"},
    )


@app.exception_handler(AuthenticationError)
@app.exception_handler(OIDCProviderException)
async def authentication_exception_handler(
    request: Request,
    exc: Union[AuthenticationError, OIDCProviderException],
):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": f"Authentication failed: {exc.name}"},
        headers={"WWW-Authenticate": "Bearer"},
    )


app.include_router(auth.router)
app.include_router(manage.router)
app.include_router(static.router)
app.include_router(dynamic.router)
