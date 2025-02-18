"""QualiCharge prefect indicators: databases."""

import logging
from typing import Optional

from pydantic import PostgresDsn
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .conf import settings
from .schemas import BaseIndicator

logger = logging.getLogger(__name__)


class Singleton(type):
    """Singleton pattern metaclass."""

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        """Store instances in a private class property."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class DBEngine(metaclass=Singleton):
    """Database engine singleton."""

    _engine: Optional[Engine] = None

    def get_engine(
        self,
        url: PostgresDsn,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
    ) -> Engine:
        """Get created engine or create a new one."""
        if self._engine is None:
            logger.debug("Create a new engine")
            self._engine = create_engine(
                str(url), echo=echo, pool_size=pool_size, max_overflow=max_overflow
            )
        logger.debug("Getting database engine %s", self._engine)
        return self._engine


def get_db_engine(
    database_url: PostgresDsn,
) -> Engine:
    """Get database engine given a database URL."""
    return DBEngine().get_engine(
        url=database_url,
        echo=settings.DEBUG,
        pool_size=settings.DB_CONNECTION_POOL_SIZE,
        max_overflow=settings.DB_CONNECTION_MAX_OVERFLOW,
    )


def get_api_db_engine() -> Engine:
    """Get the API database engine."""
    return get_db_engine(settings.API_DATABASE_URL)


def get_indicators_db_engine() -> Engine:
    """Get the Indicators database engine."""
    return get_db_engine(settings.INDICATORS_DATABASE_URL)


def create_tables():
    """Create all required tables for indicators."""
    BaseIndicator.metadata.create_all(get_indicators_db_engine())
