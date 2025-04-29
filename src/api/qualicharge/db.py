"""QualiCharge database connection."""

import logging
from typing import Generator, Optional

from pydantic import PostgresDsn
from sqlalchemy import Engine as SAEngine
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError
from sqlmodel import Session as SMSession
from sqlmodel import create_engine

from .conf import settings

logger = logging.getLogger(__name__)


class Singleton(type):
    """Singleton pattern metaclass."""

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        """Store instances in a private class property."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Engine(metaclass=Singleton):
    """Database engine singleton."""

    _engine: Optional[SAEngine] = None

    def get_engine(  # noqa: PLR0913
        self,
        url: PostgresDsn,
        echo: bool = False,
        pool_check: bool = False,
        pool_recycle: int = -1,
        pool_size: int = 10,
        max_overflow: int = 20,
    ) -> SAEngine:
        """Get created engine or create a new one."""
        if self._engine is None:
            logger.debug("Create a new engine")
            self._engine = create_engine(
                str(url),
                echo=echo,
                pool_pre_ping=pool_check,
                pool_recycle=pool_recycle,
                pool_size=pool_size,
                max_overflow=max_overflow,
            )
        logger.debug("Getting database engine %s", self._engine)
        return self._engine


class SAQueryCounter:
    """Context manager to count SQLALchemy queries.

    Inspired by: https://stackoverflow.com/a/71337784
    """

    def __init__(self, connection):
        """Initialize the counter for a given connection."""
        self.connection = connection.engine
        self.count = 0

    def __enter__(self):
        """Start listening `before_cursor_execute` event."""
        event.listen(self.connection, "before_cursor_execute", self.callback)
        return self

    def __exit__(self, *args, **kwargs):
        """Stop listening `before_cursor_execute` event."""
        event.remove(self.connection, "before_cursor_execute", self.callback)

    def callback(self, *args, **kwargs):
        """Increment the counter every time the `before_cursor_execute` event occurs."""
        self.count += 1
        logger.debug(f"Database query [{self.count=}] >> {args=} {kwargs=}")


def get_engine() -> SAEngine:
    """Get database engine."""
    return Engine().get_engine(
        url=settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_check=settings.DB_CONNECTION_POOL_CHECK,
        pool_recycle=settings.DB_CONNECTION_POOL_RECYCLE,
        pool_size=settings.DB_CONNECTION_POOL_SIZE,
        max_overflow=settings.DB_CONNECTION_MAX_OVERFLOW,
    )


def get_session() -> Generator[SMSession, None, None]:
    """Get database session."""
    with SMSession(bind=get_engine()) as session:
        logger.debug("Getting session %s", session)
        yield session


def is_alive() -> bool:
    """Check if database connection is alive."""
    session = next(get_session())
    try:
        session.execute(text("SELECT 1 as is_alive"))
        return True
    except OperationalError as err:
        logger.debug("Exception: %s", err)
        return False
