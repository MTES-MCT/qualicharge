"""QualiCharge API root."""

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pyinstrument import Profiler
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from .. import __version__
from ..conf import settings
from ..db import get_engine
from .v1 import app as v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application life span."""
    engine = get_engine()

    # Sentry
    if settings.SENTRY_DSN is not None:
        sentry_sdk.init(
            dsn=str(settings.SENTRY_DSN),
            enable_tracing=True,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            release=__version__,
            environment=settings.EXECUTION_ENVIRONMENT,
            integrations=[
                StarletteIntegration(),
                FastApiIntegration(),
            ],
        )

    yield
    engine.dispose()


app = FastAPI(title="QualiCharge", lifespan=lifespan)

if settings.PROFILING:

    @app.middleware("http")
    async def profile_request(request: Request, call_next):
        """Allow requests profiling."""
        profiling = request.query_params.get("profile", False)
        if profiling:
            profiler = Profiler(
                interval=settings.PROFILING_INTERVAL, async_mode="enabled"
            )
            profiler.start()
            await call_next(request)
            profiler.stop()
            return HTMLResponse(profiler.output_html())
        else:
            return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Mount v1 API
app.mount("/api/v1", v1)
