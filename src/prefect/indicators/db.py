"""QualiCharge prefect indicators: databases."""

import logging
from typing import Optional
from uuid import uuid4

import pandas as pd
from prefect import task
from prefect.cache_policies import NONE
from prefect.logging import get_run_logger
from pydantic import PostgresDsn
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

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


class DBEngineMixin:
    """Database engine mixin."""

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


class APIDBEngine(DBEngineMixin, metaclass=Singleton):
    """API database engine singleton."""


class IndicatorDBEngine(DBEngineMixin, metaclass=Singleton):
    """Indicators database engine singleton."""


def get_db_engine(klass, database_url: PostgresDsn) -> Engine:
    """Get database engine given a database URL."""
    return klass().get_engine(
        url=database_url,
        echo=settings.DEBUG,
        pool_size=settings.DB_CONNECTION_POOL_SIZE,
        max_overflow=settings.DB_CONNECTION_MAX_OVERFLOW,
    )


def get_api_db_engine() -> Engine:
    """Get the API database engine."""
    return get_db_engine(APIDBEngine, settings.API_DATABASE_URL)


def get_indicators_db_engine() -> Engine:
    """Get the Indicators database engine."""
    return get_db_engine(IndicatorDBEngine, settings.INDICATORS_DATABASE_URL)


@task
def create_tables():
    """Create all required tables for indicators."""
    logger = get_run_logger()
    logger.info("Will create indicator database tables…")
    engine = get_indicators_db_engine()
    logger.info(f"Database engine: {engine}")
    BaseIndicator.metadata.create_all(engine)


@task(cache_policy=NONE)
def save_indicators(name: str, indicators: pd.DataFrame):
    """Save indicators dataframe to database.

    Args:
        name (str): database table name to save data to
        indicators (Dataframe): calculated indicators
    """
    logger = get_run_logger()
    logger.info("Saving indicators to %s table…", name)

    # Ensure tables exists
    create_tables()

    # Add identifiers
    indicators["id"] = indicators.apply(lambda _: uuid4(), axis=1)

    # Replace IndicatorPeriod enums by their value
    indicators["period"] = indicators["period"].apply(lambda x: x.value)

    # Data types
    dtype = {
        c.name: c.type for c in BaseIndicator.registry.metadata.tables[name].columns
    }

    with Session(get_indicators_db_engine()) as session:
        indicators.to_sql(
            name,
            session.connection(),
            index=False,
            dtype=dtype,
            if_exists="append",
        )
        session.commit()
