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

    def get_engine(self, url: PostgresDsn, echo: bool = False) -> SAEngine:
        """Get created engine or create a new one."""
        if self._engine is None:
            logger.debug("Create a new engine")
            self._engine = create_engine(str(url), echo=echo)
        logger.debug("Getting database engine %s", self._engine)
        return self._engine


class Session(metaclass=Singleton):
    """Database session singleton."""

    _session: Optional[SMSession] = None

    def get_session(self, engine: SAEngine) -> SMSession:
        """Get active session or create a new one."""
        if self._session is None:
            logger.debug("Create new session")
            self._session = SMSession(bind=engine)
        logger.debug("Getting database session %s", self._session)
        return self._session


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
    return Engine().get_engine(url=settings.DATABASE_URL, echo=settings.DEBUG)


def get_session() -> Generator[SMSession, None, None]:
    """Get database session."""
    session = Session().get_session(get_engine())
    logger.debug("Getting session %s", session)
    try:
        yield session
    finally:
        session.close()


def is_alive() -> bool:
    """Check if database connection is alive."""
    session = next(get_session())
    try:
        session.execute(text("SELECT 1 as is_alive"))
        return True
    except OperationalError as err:
        logger.debug("Exception: %s", err)
        return False
