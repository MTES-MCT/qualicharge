"""QualiCharge schemas for administrative boundaries."""

from typing import List, Optional
from uuid import UUID, uuid4

from geoalchemy2.types import Geometry
from sqlmodel import Field, Relationship
from sqlmodel.main import SQLModelConfig

from .audit import BaseAuditableSQLModel


class BaseAdministrativeBoundaries(BaseAuditableSQLModel):
    """Base administrative boundaries model."""

    model_config = SQLModelConfig(
        validate_assignment=True, arbitrary_types_allowed=True
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(index=True, unique=True)
    name: str
    geometry: Geometry = Field(
        sa_type=Geometry(
            srid=4326,
            spatial_index=True,
        )
    )  # type: ignore[call-overload]
    population: Optional[int]
    area: Optional[float]


class Region(BaseAdministrativeBoundaries, table=True):
    """Region level (région in French)."""

    code: str = Field(regex=r"^\d{2,3}$", index=True, unique=True)

    # Relationships
    departments: List["Department"] = Relationship(back_populates="region")


class Department(BaseAdministrativeBoundaries, table=True):
    """Department level (département in French)."""

    code: str = Field(regex=r"^\d{2,3}$", index=True, unique=True)

    # Relationships
    region_id: Optional[UUID] = Field(default=None, foreign_key="region.id")
    region: Region = Relationship(back_populates="departments")

    cities: List["City"] = Relationship(back_populates="department")


class EPCI(BaseAdministrativeBoundaries, table=True):
    """Groupment of cities level (French)."""

    code: str = Field(regex=r"^\d{9}$", index=True, unique=True)

    # Relationships
    cities: List["City"] = Relationship(back_populates="epci")


class City(BaseAdministrativeBoundaries, table=True):
    """City level (communes in French)."""

    code: str = Field(regex=r"^\d{5}$", index=True, unique=True)

    # Relationships
    department_id: Optional[UUID] = Field(default=None, foreign_key="department.id")
    department: Department = Relationship(back_populates="cities")

    epci_id: Optional[UUID] = Field(default=None, foreign_key="epci.id")
    epci: EPCI = Relationship(back_populates="cities")
