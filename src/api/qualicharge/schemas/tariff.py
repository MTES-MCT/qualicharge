"""QualiCharge tariff SQL schemas."""

from typing import List, Optional
from uuid import UUID, uuid4

from pydantic.types import AwareDatetime
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import Column as SAColumn
from sqlalchemy.types import DateTime
from sqlmodel import Field, Relationship

from qualicharge.models.fields import IdPdcItinerance
from qualicharge.models.tariff import TariffRead

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
    original_last_updated: AwareDatetime = Field(
        sa_column=SAColumn(DateTime(timezone=True), index=True, nullable=False),
    )
    raw: dict = Field(sa_column=SAColumn(JSONB, nullable=False))
    start: AwareDatetime = Field(
        sa_column=SAColumn(DateTime(timezone=True), index=True, nullable=False),
    )
    end: Optional[AwareDatetime] = Field(
        sa_column=SAColumn(DateTime(timezone=True), index=True, nullable=True),
    )

    points_de_charge: List[PointDeCharge] = Relationship(
        link_model=PointDeChargeTariff,
    )

    def to_read(self, ids_pdc_itinerance: list[IdPdcItinerance]) -> TariffRead:
        """Convert this tariff to an API response using it's list of IdPdcItinerance."""
        return TariffRead(
            id=str(self.id),
            original_id=self.original_id,
            original_last_updated=self.original_last_updated,
            raw=self.raw,
            start=self.start,
            end=self.end,
            id_pdc_itinerance=ids_pdc_itinerance,
        )
