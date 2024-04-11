"""QualiCharge API v1."""

import logging
from typing import Union

from fastapi import FastAPI, Request, Security, status
from fastapi.responses import JSONResponse

from qualicharge.auth.oidc import get_token
from qualicharge.exceptions import OIDCAuthenticationError, OIDCProviderException

from .routers import auth, static

logger = logging.getLogger(__name__)

app = FastAPI(title="QualiCharge API (v1)", dependencies=[Security(get_token)])


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


app.include_router(auth.router)
app.include_router(static.router)
