"""QualiCharge API root."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..conf import settings
from ..db import get_engine
from .v1 import app as v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application life span."""
    engine = get_engine()
    yield
    engine.dispose()


app = FastAPI(title="QualiCharge", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Mount v1 API
app.mount("/api/v1", v1)
