"""QualiCharge prefect indicators: databases."""

import logging
from functools import cache
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
from .schemas import BaseIndicator, declare_environment_schemas
from .types import Environment

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


@cache
def get_api_db_engine(environment: Environment) -> Engine:
    """Get the API database engine for an environment."""
    return create_engine(
        str(settings.API_DATABASE_URLS[environment]),
        echo=settings.DEBUG,
        pool_size=settings.DB_CONNECTION_POOL_SIZE,
        max_overflow=settings.DB_CONNECTION_MAX_OVERFLOW,
    )


def get_indicators_db_engine() -> Engine:
    """Get the Indicators database engine."""
    return get_db_engine(IndicatorDBEngine, settings.INDICATORS_DATABASE_URL)


@task
def create_tables():
    """Create all required tables for indicators."""
    logger = get_run_logger()
    logger.info("Will create indicator database tables…")

    logger.info("Declaring schemas for active environments…")
    declare_environment_schemas()

    engine = get_indicators_db_engine()
    logger.info(f"Database engine: {engine}")

    logger.info(f"Registered tables: {BaseIndicator.metadata.tables}")
    BaseIndicator.metadata.create_all(engine)


@task(cache_policy=NONE)
def save_indicators(environment: Environment, indicators: pd.DataFrame):
    """Save indicators dataframe to database.

    Args:
        environment (Environment): database table name to save data to
        indicators (Dataframe): calculated indicators
    """
    logger = get_run_logger()
    df = indicators.copy()

    table_name = environment.value
    logger.info("Saving indicators to %s table…", table_name)

    # Ensure tables exists
    create_tables()

    # Add identifiers
    df["id"] = df.apply(lambda _: uuid4(), axis=1)

    # Replace IndicatorPeriod enums by their value
    df["period"] = df["period"].apply(lambda x: x.value)

    # Data types
    dtype = {
        c.name: c.type
        for c in BaseIndicator.registry.metadata.tables[table_name].columns
    }

    with Session(get_indicators_db_engine()) as session:
        df.to_sql(
            table_name,
            session.connection(),
            index=False,
            dtype=dtype,  # type: ignore
            if_exists="append",
        )
        session.commit()
