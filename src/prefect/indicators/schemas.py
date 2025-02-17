"""QualiCharge prefect indicators: schemas."""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime, Float, SmallInteger, String

from .conf import settings

logger = logging.getLogger(__name__)


class BaseIndicator(DeclarativeBase):
    """Base indicator model."""

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    code: Mapped[str] = mapped_column(String(5))
    level: Mapped[int] = mapped_column(SmallInteger)
    target: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    period: Mapped[str] = mapped_column(String(1))
    value: Mapped[float] = mapped_column(Float)
    extras: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        """Indicator representation."""
        return (
            f"{self.__tablename__}/{self.id}: "
            f"{self.code}-{self.period}-{self.level}-{self.target}-{self.category}"
        )


def declare_environment_schemas():
    """Declare schemas for every active environment.

    When calling this utility, you will declare a new schema per active environment:

    class Production(BaseIndicator):
        __tablename__ = "production"
    """
    logger.info("Will declare indicators schemas...")
    for environment in settings.API_ACTIVE_ENVIRONMENTS:
        schema = environment.value.title()

        # Schema has already been defined
        if schema in globals():
            continue

        globals()[schema] = type(
            schema, (BaseIndicator,), {"__tablename__": environment.value}
        )
        logger.info("New schema: %s", schema)
