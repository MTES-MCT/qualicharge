"""QualiCharge tariff SQL schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import Column as SAColumn
from sqlmodel import Field, Relationship

from . import BaseAuditableSQLModel, SoftDeleteMixin
from .core import PointDeCharge


class PointDeChargeTariff(BaseAuditableSQLModel, table=True):
    """Many-to-many association between charge points and tariffs."""

    point_de_charge_id: UUID = Field(
        foreign_key="_pointdecharge.id",
        primary_key=True,
    )
    tariff_id: UUID = Field(
        foreign_key="tariff.id",
        primary_key=True,
    )


class Tariff(SoftDeleteMixin, BaseAuditableSQLModel, table=True):
    """Tariff stored from operator input."""

    __table_args__ = BaseAuditableSQLModel.__table_args__ + (
        UniqueConstraint(
            "original_id",
            "original_last_updated",
            name="tariff_original_id_original_last_updated_key",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    original_id: str = Field(index=True)
    original_last_updated: datetime = Field(index=True)
    raw: dict = Field(sa_column=SAColumn(JSONB, nullable=False))
    start: datetime = Field(index=True)
    end: Optional[datetime] = Field(default=None, index=True)

    points_de_charge: List[PointDeCharge] = Relationship(
        link_model=PointDeChargeTariff,
    )
