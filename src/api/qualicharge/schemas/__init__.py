"""QualiCharge schemas."""

from datetime import datetime, timezone
from typing import Any, List, Optional, Union
from uuid import UUID, uuid4

from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry, WKBElement
from pydantic import (
    EmailStr,
    PastDate,
    PastDatetime,
    PositiveFloat,
    PositiveInt,
    ValidationInfo,
    field_serializer,
    field_validator,
)
from pydantic_extra_types.coordinate import Coordinate
from shapely.geometry import mapping
from sqlalchemy import CheckConstraint
from sqlalchemy.types import Date, DateTime, String
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint
from sqlmodel.main import SQLModelConfig

from ..models.dynamic import SessionBase, StatusBase
from ..models.static import (
    AccessibilitePMREnum,
    ConditionAccesEnum,
    DataGouvCoordinate,
    FrenchPhoneNumber,
    ImplantationStationEnum,
    RaccordementEnum,
)


class BaseTimestampedSQLModel(SQLModel):
    """A base class for SQL models with timestamp fields.

    This class provides two timestamp fields, `created_at` and `updated_at`, which are
    automatically managed. The `created_at` field is set to the current UTC time when
    a new record is created, and the `updated_at` field is updated to the current UTC
    time whenever the record is modified.
    """

    __table_args__: Any = (
        CheckConstraint("created_at <= updated_at", name="pre-creation-update"),
    )

    created_at: PastDatetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp indicating when the record was created.",
    )  # type: ignore
    updated_at: PastDatetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp indicating when the record was last updated.",
    )  # type: ignore


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

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("nom_amenageur", "siren_amenageur", "contact_amenageur")
        return all(getattr(self, field) == getattr(other, field) for field in fields)


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

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("nom_operateur", "contact_operateur", "telephone_operateur")
        return all(getattr(self, field) == getattr(other, field) for field in fields)


class Enseigne(BaseTimestampedSQLModel, table=True):
    """Enseigne table."""

    model_config = SQLModelConfig(validate_assignment=True)

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    nom_enseigne: str = Field(unique=True)

    # Relationships
    stations: List["Station"] = Relationship(back_populates="enseigne")

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("nom_enseigne",)
        return all(getattr(self, field) == getattr(other, field) for field in fields)


class Localisation(BaseTimestampedSQLModel, table=True):
    """Localisation table."""

    model_config = SQLModelConfig(
        validate_assignment=True, arbitrary_types_allowed=True
    )

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    adresse_station: str = Field(unique=True)
    code_insee_commune: Optional[str] = Field(regex=r"^([013-9]\d|2[AB1-9])\d{3}$")
    coordonneesXY: DataGouvCoordinate = Field(
        sa_type=Geometry(
            geometry_type="POINT",
            # WGS84 coordinates system
            srid=4326,
            spatial_index=True,
        ),
    )  # type: ignore

    # Relationships
    stations: List["Station"] = Relationship(back_populates="localisation")

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("adresse_station",)
        return all(getattr(self, field) == getattr(other, field) for field in fields)

    @staticmethod
    def _coordinates_to_geometry_point(value: Coordinate):
        """Convert coordinate to Geometry point."""
        return f"POINT({value.longitude} {value.latitude})"

    @staticmethod
    def _wkb_to_coordinates(value: WKBElement):
        """Convert WKB to Coordinate."""
        return Coordinate(*reversed(mapping(to_shape(value)).get("coordinates")))

    @field_validator("coordonneesXY")
    @classmethod
    def set_geometry_point(cls, value: Coordinate, info: ValidationInfo) -> str:
        """Set coordonneesXY geometry from Coordinate type."""
        return cls._coordinates_to_geometry_point(value)

    @field_serializer("coordonneesXY")
    def serialize_coordonneesXY(
        self, value: Union[str, WKBElement], _
    ) -> Union[str, Coordinate]:
        """Serialize coordonneesXY field.

        If value is a string, we suppose that the SQLModel has been instanciated from a
        Coordinate instance and converted to a Geometry WKT Point(long lat) definition.
        This is the expected behavior to save the schema to database as this
        serialization will be used in SQL requests.

        By default, we expect the value to be a Geometry (WKB) field. In this case, its
        value has been set from the database. In this case, it means that we expect it
        to be serialized as a Coordinate instance.
        """
        # POINT(long lat) string case
        if isinstance(value, str):
            return value
        # Geometry type case (default)
        return self._wkb_to_coordinates(value)


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
    raccordement: Optional[RaccordementEnum]
    num_pdl: Optional[str] = Field(regex=r"^\d{14}$")
    date_maj: PastDate = Field(sa_type=Date)
    date_mise_en_service: Optional[PastDate] = Field(sa_type=Date)

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

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("id_station_itinerance",)
        return all(getattr(self, field) == getattr(other, field) for field in fields)


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

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("id_pdc_itinerance",)
        return all(getattr(self, field) == getattr(other, field) for field in fields)

    # Relationships
    station_id: Optional[UUID] = Field(default=None, foreign_key="station.id")
    station: Station = Relationship(back_populates="points_de_charge")
    sessions: List["Session"] = Relationship(back_populates="point_de_charge")
    statuses: List["Status"] = Relationship(back_populates="point_de_charge")


class Session(BaseTimestampedSQLModel, SessionBase, table=True):
    """IRVE recharge session."""

    __table_args__ = BaseTimestampedSQLModel.__table_args__ + (
        {"timescaledb_hypertable": {"time_column_name": "start"}},
    )

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    start: PastDatetime = Field(
        sa_type=DateTime(timezone=True),
        description="The timestamp indicating when the session started.",
    )  # type: ignore
    end: PastDatetime = Field(
        sa_type=DateTime(timezone=True),
        description="The timestamp indicating when the session ended.",
    )  # type: ignore

    # Relationships
    point_de_charge_id: Optional[UUID] = Field(
        default=None, foreign_key="pointdecharge.id"
    )
    point_de_charge: PointDeCharge = Relationship(back_populates="sessions")


class Status(BaseTimestampedSQLModel, StatusBase, table=True):
    """IRVE recharge session."""

    __table_args__ = BaseTimestampedSQLModel.__table_args__ + (
        {"timescaledb_hypertable": {"time_column_name": "horodatage"}},
    )

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    horodatage: PastDatetime = Field(
        sa_type=DateTime(timezone=True),
        description="The timestamp indicating when the status changed.",
    )  # type: ignore

    # Relationships
    point_de_charge_id: Optional[UUID] = Field(
        default=None, foreign_key="pointdecharge.id"
    )
    point_de_charge: PointDeCharge = Relationship(back_populates="statuses")
