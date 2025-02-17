"""QualiCharge prefect indicators: schemas."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime, Float, SmallInteger, String


class BaseIndicator(DeclarativeBase):
    """Base indicator model."""

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    category: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(5))
    level: Mapped[int] = mapped_column(SmallInteger)
    target: Mapped[Optional[str]] = mapped_column(String(100))
    period: Mapped[str] = mapped_column(String(1))
    value: Mapped[float] = mapped_column(Float)
    extras: Mapped[Optional[dict]] = mapped_column(JSONB)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        """Indicator representation."""
        return (
                f"{self.__tablename__}/{self.id}: "
                f"{self.code}-{self.period}-{self.level}-{self.target}-{self.category}"
        )


class Staging(BaseIndicator):
    """Indicators running on the Staging API database."""

    __tablename__ = "staging"


class Production(BaseIndicator):
    """Indicators running on the Staging API database."""

    __tablename__ = "production"
