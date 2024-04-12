"""QualiCharge static schemas."""

from typing import List, Optional
from uuid import UUID, uuid4

from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry
from pydantic import (
    EmailStr,
    PositiveFloat,
    PositiveInt,
    ValidationInfo,
    field_serializer,
    field_validator,
)
from pydantic.types import PastDate
from pydantic_extra_types.coordinate import Coordinate
from shapely.geometry import mapping
from sqlalchemy.types import DateTime, String
from sqlmodel import Field, Relationship, UniqueConstraint
from sqlmodel.main import SQLModelConfig

from ..models.static import (
    AccessibilitePMREnum,
    ConditionAccesEnum,
    FrenchPhoneNumber,
    ImplantationStationEnum,
    RaccordementEmum,
)
from . import BaseTimestampedSQLModel


class Amenageur(BaseTimestampedSQLModel, table=True):
    """Amenageur table."""

    __table_args__ = BaseTimestampedSQLModel.__table_args__ + (
        UniqueConstraint("nom_amenageur", "siren_amenageur", "contact_amenageur"),
    )

    model_config = SQLModelConfig(validate_assignment=True)

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    nom_amenageur: Optional[str]
    siren_amenageur: Optional[str] = Field(regex=r"^\d{9}$")
    contact_amenageur: Optional[EmailStr] = Field(sa_type=String)

    # Relationships
    stations: List["Station"] = Relationship(back_populates="amenageur")


class Operateur(BaseTimestampedSQLModel, table=True):
    """Operateur table."""

    __table_args__ = BaseTimestampedSQLModel.__table_args__ + (
        UniqueConstraint("nom_operateur", "contact_operateur", "telephone_operateur"),
    )

    model_config = SQLModelConfig(validate_assignment=True)

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    nom_operateur: Optional[str]
    contact_operateur: EmailStr = Field(sa_type=String)
    telephone_operateur: Optional[FrenchPhoneNumber]

    # Relationships
    stations: List["Station"] = Relationship(back_populates="operateur")


class Enseigne(BaseTimestampedSQLModel, table=True):
    """Enseigne table."""

    model_config = SQLModelConfig(validate_assignment=True)

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    nom_enseigne: str = Field(unique=True)

    # Relationships
    stations: List["Station"] = Relationship(back_populates="enseigne")


class Localisation(BaseTimestampedSQLModel, table=True):
    """Localisation table."""

    __table_args__ = BaseTimestampedSQLModel.__table_args__ + (
        UniqueConstraint("adresse_station", "coordonneesXY"),
    )

    model_config = SQLModelConfig(
        validate_assignment=True, arbitrary_types_allowed=True
    )

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    adresse_station: str
    code_insee_commune: Optional[str] = Field(regex=r"^([013-9]\d|2[AB1-9])\d{3}$")
    coordonneesXY: Coordinate = Field(
        sa_type=Geometry(
            geometry_type="POINT",
            # WGS84 coordinates system
            srid=4326,
            spatial_index=True,
        ),
    )  # type: ignore

    # Relationships
    stations: List["Station"] = Relationship(back_populates="localisation")

    @field_validator("coordonneesXY")
    @classmethod
    def set_geometry_point(cls, value: Coordinate, info: ValidationInfo) -> str:
        """Set coordonneesXY geometry from Coordinate type."""
        return f"POINT({value.longitude} {value.latitude})"

    @field_serializer("coordonneesXY")
    def serialize_wkb_point(self, wkb, _):
        """Serialize WKB element (Point type geometry) field to coordinates."""
        # Coordinate type expects a (latitude, longitude) tuple as input, so we need to
        # reverse the original tuple as the standard is (longitude, latitude).
        return Coordinate(*reversed(mapping(to_shape(wkb)).get("coordinates")))


class Station(BaseTimestampedSQLModel, table=True):
    """Station table."""

    model_config = SQLModelConfig(validate_assignment=True)

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    id_station_itinerance: str = Field(
        regex="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$",
        index=True,
        unique=True,
    )
    id_station_local: Optional[str]
    nom_station: str
    implantation_station: ImplantationStationEnum
    nbre_pdc: PositiveInt
    condition_acces: ConditionAccesEnum
    horaires: str = Field(regex=r"(.*?)((\d{1,2}:\d{2})-(\d{1,2}:\d{2})|24/7)")
    station_deux_roues: bool
    raccordement: Optional[RaccordementEmum]
    num_pdl: Optional[str] = Field(regex=r"^\d{14}$")
    date_maj: PastDate = Field(sa_type=DateTime)
    date_mise_en_service: Optional[PastDate] = Field(sa_type=DateTime)

    # Relationships
    amenageur_id: Optional[UUID] = Field(default=None, foreign_key="amenageur.id")
    amenageur: Amenageur = Relationship(back_populates="stations")

    operateur_id: Optional[UUID] = Field(default=None, foreign_key="operateur.id")
    operateur: Operateur = Relationship(back_populates="stations")

    enseigne_id: Optional[UUID] = Field(default=None, foreign_key="enseigne.id")
    enseigne: Enseigne = Relationship(back_populates="stations")

    localisation_id: Optional[UUID] = Field(default=None, foreign_key="localisation.id")
    localisation: Localisation = Relationship(back_populates="stations")

    points_de_charge: List["PointDeCharge"] = Relationship(back_populates="station")


class PointDeCharge(BaseTimestampedSQLModel, table=True):
    """PointDeCharge table."""

    model_config = SQLModelConfig(validate_assignment=True)

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    id_pdc_itinerance: str = Field(
        regex="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$", index=True
    )
    id_pdc_local: Optional[str]
    puissance_nominale: PositiveFloat
    prise_type_ef: bool
    prise_type_2: bool
    prise_type_combo_ccs: bool
    prise_type_chademo: bool
    prise_type_autre: bool
    gratuit: Optional[bool]
    paiement_acte: bool
    paiement_cb: Optional[bool]
    paiement_autre: Optional[bool]
    tarification: Optional[str]
    reservation: bool
    accessibilite_pmr: AccessibilitePMREnum
    restriction_gabarit: str
    observations: Optional[str]
    cable_t2_attache: Optional[bool]

    # Relationships
    station_id: Optional[UUID] = Field(default=None, foreign_key="station.id")
    station: Station = Relationship(back_populates="points_de_charge")
