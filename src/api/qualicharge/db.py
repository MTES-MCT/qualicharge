"""QualiCharge database connection."""

import logging
from typing import Generator, Optional

from pydantic import PostgresDsn
from sqlalchemy import Engine as SAEngine
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine as SAAsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Session as SMSession
from sqlmodel import create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

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


class BaseEngine(metaclass=Singleton):
    """Base database engine."""

    _engine: Optional[SAEngine | SAAsyncEngine] = None

    def __init__(
        self,
        url: PostgresDsn,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
    ):
        """Set engine kwargs."""
        self.kwargs: dict = {
            "url": str(url),
            "echo": echo,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
        }

    @staticmethod
    def create(*args, **kwargs) -> SAEngine | SAAsyncEngine:
        """An engine should define how it will be created.

        We cannot use both the singleton and abstract metaclasses,
        hence we use this old trick.
        """
        raise NotImplementedError("An engine should define a create static method.")

    def get_engine(self) -> SAEngine | SAAsyncEngine:
        """Get database engine."""
        if self._engine is None:
            url = self.kwargs.pop("url")
            logger.debug(f"Create a new engine using {url=} and {self.kwargs=}")
            self._engine = self.create(url, **self.kwargs)

        logger.debug("Getting database engine %s", self._engine)
        return self._engine


class Engine(BaseEngine):
    """Database engine singleton."""

    @staticmethod
    def create(*args, **kwargs) -> SAEngine:
        """Create a synchronous database engine."""
        return create_engine(*args, **kwargs)


class AsyncEngine(BaseEngine):
    """Database asynchronous engine singleton."""

    def __init__(self, *args, **kwargs) -> None:
        """Add extra kwargs."""
        super().__init__(*args, **kwargs)
        self.kwargs.update(
            {
                "connect_args": {"server_settings": {"jit": "off"}},
            }
        )

    @staticmethod
    def create(*args, **kwargs) -> SAAsyncEngine:
        """Create an asynchronous database engine."""
        return create_async_engine(*args, **kwargs)


class SAQueryCounter:
    """Context manager to count SQLALchemy queries.

    Inspired by: https://stackoverflow.com/a/71337784
    """

    def __init__(self, connection):
        """Initialize the counter for a given connection."""
        self.connection = connection.engine
        self.count = 0

    async def __aenter__(self):
        """Start listening `before_cursor_execute` event."""
        event.listen(self.connection, "before_cursor_execute", self.callback)
        return self

    async def __aexit__(self, *args, **kwargs):
        """Stop listening `before_cursor_execute` event."""
        event.remove(self.connection, "before_cursor_execute", self.callback)

    def callback(self, *args, **kwargs):
        """Increment the counter every time the `before_cursor_execute` event occurs."""
        self.count += 1
        logger.debug(f"Database query [{self.count=}] >> {args=} {kwargs=}")


def get_engine(async_: bool = False) -> SAAsyncEngine | SAEngine:
    """Get database engine."""
    kwargs = {
        "url": settings.ASYNC_DATABASE_URL if async_ else settings.DATABASE_URL,
        "echo": settings.DEBUG,
        "pool_size": settings.DB_CONNECTION_POOL_SIZE,
        "max_overflow": settings.DB_CONNECTION_MAX_OVERFLOW,
    }
    Klass = AsyncEngine if async_ else Engine
    return Klass(**kwargs).get_engine()


async def get_async_session() -> AsyncSession:
    """Get async database session."""
    async with AsyncSession(bind=get_engine(async_=True)) as session:
        logger.debug("Getting session %s", session)
        yield session


def get_session() -> Generator[SMSession, None, None]:
    """Get database session."""
    with SMSession(bind=get_engine(async_=False)) as session:
        logger.debug("Getting session %s", session)
        yield session


async def is_alive() -> bool:
    """Check if database connection is alive."""
    session = await get_async_session()
    try:
        await session.execute(text("SELECT 1 as is_alive"))
        return True
    except OperationalError as err:
        logger.debug("Exception: %s", err)
        return False
