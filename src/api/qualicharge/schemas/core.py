"""QualiCharge core statique and dynamique schemas."""

from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar, List, Optional, Union, cast
from uuid import UUID, uuid4

from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry, WKBElement
from pydantic import (
    EmailStr,
    PastDatetime,
    PositiveFloat,
    PositiveInt,
    ValidationInfo,
    computed_field,
    field_serializer,
    field_validator,
)
from pydantic_extra_types.coordinate import Coordinate
from shapely.geometry import mapping
from sqlalchemy import Select, event
from sqlalchemy import cast as SA_cast
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import registry
from sqlalchemy.schema import Column as SAColumn
from sqlalchemy.schema import Index
from sqlalchemy.types import Date, DateTime, String
from sqlalchemy_utils import create_materialized_view
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint, select
from sqlmodel import Session as SMSession
from sqlmodel.main import SQLModelConfig

from qualicharge.exceptions import ObjectDoesNotExist

from ..models.dynamic import (
    EtatPDCEnum,
    EtatPriseEnum,
    OccupationPDCEnum,
    SessionBase,
    StatusBase,
)
from ..models.static import (
    AccessibilitePMREnum,
    ConditionAccesEnum,
    DataGouvCoordinate,
    FrenchPhoneNumber,
    ImplantationStationEnum,
    NotFutureDate,
    RaccordementEnum,
    Statique,
)
from . import BaseAuditableSQLModel, BaseTimestampedSQLModel

if TYPE_CHECKING:
    from qualicharge.auth.schemas import Group

mapper_registry = registry()

STATIQUE_MV_TABLE_NAME: str = "statique"

DEFAULT_SRID: int = 4326


class OperationalUnitTypeEnum(IntEnum):
    """Operational unit types."""

    CHARGING = 1
    MOBILITY = 2


# Enum definition for database: we want to store Enum values instead of keys (this is
# the default behavior).
def get_enum_values(enum_):
    """Get enum values."""
    return [m.value for m in enum_]


ImplantationStationDBEnum: PgEnum = PgEnum(
    ImplantationStationEnum,
    name="implantation_station_enum",
    values_callable=get_enum_values,
)

ConditionAccesDBEnum: PgEnum = PgEnum(
    ConditionAccesEnum,
    name="condition_acces_enum",
    values_callable=get_enum_values,
)

AccessibilitePMRDBEnum: PgEnum = PgEnum(
    AccessibilitePMREnum,
    name="accessibilite_pmr_enum",
    values_callable=get_enum_values,
)

RaccordementDBEnum: PgEnum = PgEnum(
    RaccordementEnum,
    name="raccordement_enum",
    values_callable=get_enum_values,
)

EtatPDCDBEnum: PgEnum = PgEnum(
    EtatPDCEnum,
    name="etat_pdc_enum",
    values_callable=get_enum_values,
)

EtatPriseDBEnum: PgEnum = PgEnum(
    EtatPriseEnum,
    name="etat_prise_enum",
    values_callable=get_enum_values,
)

OccupationPDCDBEnum: PgEnum = PgEnum(
    OccupationPDCEnum,
    name="occupation_pdc_enum",
    values_callable=get_enum_values,
)


class Amenageur(BaseAuditableSQLModel, table=True):
    """Amenageur table."""

    __table_args__ = BaseAuditableSQLModel.__table_args__ + (
        UniqueConstraint("nom_amenageur", "siren_amenageur", "contact_amenageur"),
    )

    model_config = SQLModelConfig(validate_assignment=True)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    nom_amenageur: Optional[str]
    siren_amenageur: Optional[str] = Field(regex=r"^\d{9}$")
    contact_amenageur: Optional[EmailStr] = Field(sa_type=String)

    # Relationships
    stations: List["Station"] = Relationship(back_populates="amenageur")

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("nom_amenageur", "siren_amenageur", "contact_amenageur")
        return all(getattr(self, field) == getattr(other, field) for field in fields)


class Operateur(BaseAuditableSQLModel, table=True):
    """Operateur table."""

    __table_args__ = BaseAuditableSQLModel.__table_args__ + (
        UniqueConstraint("nom_operateur", "contact_operateur", "telephone_operateur"),
    )

    model_config = SQLModelConfig(validate_assignment=True)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    nom_operateur: Optional[str]
    contact_operateur: EmailStr = Field(sa_type=String)
    telephone_operateur: Optional[FrenchPhoneNumber]

    # Relationships
    stations: List["Station"] = Relationship(back_populates="operateur")

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("nom_operateur", "contact_operateur", "telephone_operateur")
        return all(getattr(self, field) == getattr(other, field) for field in fields)


class Enseigne(BaseAuditableSQLModel, table=True):
    """Enseigne table."""

    model_config = SQLModelConfig(validate_assignment=True)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    nom_enseigne: str = Field(unique=True)

    # Relationships
    stations: List["Station"] = Relationship(back_populates="enseigne")

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("nom_enseigne",)
        return all(getattr(self, field) == getattr(other, field) for field in fields)


class Localisation(BaseAuditableSQLModel, table=True):
    """Localisation table."""

    model_config = SQLModelConfig(
        validate_assignment=True, arbitrary_types_allowed=True
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    adresse_station: str
    code_insee_commune: str = Field(regex=r"^([013-9]\d|2[AB1-9])\d{3}$")
    coordonneesXY: DataGouvCoordinate = Field(
        sa_type=Geometry(
            geometry_type="POINT",
            # WGS84 coordinates system
            srid=DEFAULT_SRID,
            spatial_index=True,
        ),
        unique=True,
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
        return f"SRID={DEFAULT_SRID};POINT({value.longitude} {value.latitude})"

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


class OperationalUnit(BaseTimestampedSQLModel, table=True):
    """OperationalUnit table."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(
        regex="^[A-Z]{2}[A-Z0-9]{3}$",
        index=True,
        unique=True,
    )
    name: str
    type: OperationalUnitTypeEnum

    # Relationships
    stations: List["Station"] = Relationship(back_populates="operational_unit")
    groups: List["Group"] = Relationship(
        back_populates="operational_units",
        sa_relationship_kwargs={"secondary": "groupoperationalunit"},
    )

    def create_stations_fk(self, session: SMSession):
        """Create linked stations foreign keys."""
        stations = session.exec(
            select(Station).where(
                cast(SAColumn, Station.id_station_itinerance).regexp_match(
                    f"^{self.code}P.*$"
                )
            )
        ).all()

        # No matching station!
        if not len(stations):
            return

        for station in stations:
            station.operational_unit_id = self.id
        session.add_all(stations)
        session.commit()


class Station(BaseAuditableSQLModel, table=True):
    """Station table."""

    model_config = SQLModelConfig(validate_assignment=True)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    id_station_itinerance: str = Field(
        regex="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$",
        index=True,
        unique=True,
    )
    id_station_local: Optional[str]
    nom_station: str
    implantation_station: ImplantationStationEnum = Field(
        sa_column=SAColumn(ImplantationStationDBEnum, nullable=False)
    )
    nbre_pdc: PositiveInt
    condition_acces: ConditionAccesEnum = Field(
        sa_column=SAColumn(ConditionAccesDBEnum, nullable=False)
    )
    horaires: str = Field(regex=r"(.*?)((\d{1,2}:\d{2})-(\d{1,2}:\d{2})|24/7)")
    station_deux_roues: bool
    raccordement: Optional[RaccordementEnum] = Field(
        sa_column=SAColumn(RaccordementDBEnum, nullable=True)
    )
    num_pdl: Optional[str] = Field(max_length=64)
    date_maj: NotFutureDate = Field(sa_type=Date)
    date_mise_en_service: Optional[NotFutureDate] = Field(sa_type=Date)

    # Relationships
    amenageur_id: Optional[UUID] = Field(
        default=None,
        foreign_key="amenageur.id",
        ondelete="SET NULL",
    )
    amenageur: Amenageur = Relationship(back_populates="stations")

    operateur_id: Optional[UUID] = Field(
        default=None,
        foreign_key="operateur.id",
        ondelete="SET NULL",
    )
    operateur: Operateur = Relationship(back_populates="stations")

    enseigne_id: Optional[UUID] = Field(
        default=None,
        foreign_key="enseigne.id",
        ondelete="SET NULL",
    )
    enseigne: Enseigne = Relationship(back_populates="stations")

    localisation_id: Optional[UUID] = Field(
        default=None,
        foreign_key="localisation.id",
        ondelete="SET NULL",
    )
    localisation: Localisation = Relationship(back_populates="stations")

    operational_unit_id: Optional[UUID] = Field(
        default=None,
        foreign_key="operationalunit.id",
        ondelete="SET NULL",
    )
    operational_unit: OperationalUnit = Relationship(back_populates="stations")

    points_de_charge: List["PointDeCharge"] = Relationship(back_populates="station")

    def __eq__(self, other) -> bool:
        """Assess instances equality given uniqueness criterions."""
        fields = ("id_station_itinerance",)
        return all(getattr(self, field) == getattr(other, field) for field in fields)


@event.listens_for(Station, "before_insert")
@event.listens_for(Station, "before_update")
def link_station_to_operational_unit(mapper, connection, target):
    """Automatically link station to an operational unit."""
    code = target.id_station_itinerance[:5]
    operational_unit = connection.execute(
        select(OperationalUnit).where(OperationalUnit.code == code)
    ).one_or_none()
    if operational_unit is None:
        raise ObjectDoesNotExist(
            f"OperationalUnit with code {code} should be created first"
        )
    target.operational_unit_id = operational_unit.id


class PointDeCharge(BaseAuditableSQLModel, table=True):
    """PointDeCharge table."""

    model_config = SQLModelConfig(validate_assignment=True)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    id_pdc_itinerance: str = Field(
        regex="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$",
        index=True,
        unique=True,
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
    accessibilite_pmr: AccessibilitePMREnum = Field(
        sa_column=SAColumn(AccessibilitePMRDBEnum, nullable=False)
    )
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


class Session(BaseAuditableSQLModel, SessionBase, table=True):
    """IRVE recharge session."""

    __table_args__ = BaseAuditableSQLModel.__table_args__ + (
        {"timescaledb_hypertable": {"time_column_name": "start"}},
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
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

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    horodatage: PastDatetime = Field(
        sa_type=DateTime(timezone=True),
        description="The timestamp indicating when the status changed.",
    )  # type: ignore

    etat_pdc: EtatPDCEnum = Field(sa_column=SAColumn(EtatPDCDBEnum, nullable=False))
    occupation_pdc: OccupationPDCEnum = Field(
        sa_column=SAColumn(OccupationPDCDBEnum, nullable=False)
    )
    etat_prise_type_2: Optional[EtatPriseEnum] = Field(
        sa_column=SAColumn(EtatPriseDBEnum, nullable=True)
    )
    etat_prise_type_combo_ccs: Optional[EtatPriseEnum] = Field(
        sa_column=SAColumn(EtatPriseDBEnum, nullable=True)
    )
    etat_prise_type_chademo: Optional[EtatPriseEnum] = Field(
        sa_column=SAColumn(EtatPriseDBEnum, nullable=True)
    )
    etat_prise_type_ef: Optional[EtatPriseEnum] = Field(
        sa_column=SAColumn(EtatPriseDBEnum, nullable=True)
    )

    # Relationships
    point_de_charge_id: Optional[UUID] = Field(
        default=None, foreign_key="pointdecharge.id"
    )
    point_de_charge: PointDeCharge = Relationship(back_populates="statuses")

    @computed_field  # type: ignore[misc]
    @property
    def id_pdc_itinerance(self) -> str:
        """Return the PointDeCharge.id_pdc_itinerance (used for serialization only)."""
        return self.point_de_charge.id_pdc_itinerance


class StatiqueMV(Statique, SQLModel):
    """Statique Materialized View."""

    __tablename__ = STATIQUE_MV_TABLE_NAME

    model_config = SQLModel.model_config

    pdc_id: UUID
    pdc_updated_at: datetime

    # WKBElement to Coordinate
    @field_serializer("coordonneesXY")
    @staticmethod
    def _wkb_to_coordinates(value: WKBElement):
        """Convert WKB to Coordinate."""
        return Localisation._wkb_to_coordinates(value)


class _StatiqueMV(SQLModel):
    """Statique Materialized view.

    NOTE: This is an internal model used **ONLY** for creating the materialized view.
    """

    selectable: ClassVar[Select] = (
        select(  # type: ignore[call-overload, misc]
            cast(SAColumn, PointDeCharge.id).label("pdc_id"),
            cast(SAColumn, PointDeCharge.updated_at).label("pdc_updated_at"),
            Amenageur.nom_amenageur,
            Amenageur.siren_amenageur,
            Amenageur.contact_amenageur,
            Operateur.nom_operateur,
            Operateur.contact_operateur,
            Operateur.telephone_operateur,
            Enseigne.nom_enseigne,
            Station.id_station_itinerance,
            Station.id_station_local,
            Station.nom_station,
            Station.implantation_station,
            Localisation.adresse_station,
            Localisation.code_insee_commune,
            SA_cast(
                Localisation.coordonneesXY,
                Geometry(
                    geometry_type="POINT",
                    # WGS84 coordinates system
                    srid=4326,
                    spatial_index=False,
                ),
            ).label("coordonneesXY"),
            Station.nbre_pdc,
            PointDeCharge.id_pdc_itinerance,
            PointDeCharge.id_pdc_local,
            PointDeCharge.puissance_nominale,
            PointDeCharge.prise_type_ef,
            PointDeCharge.prise_type_2,
            PointDeCharge.prise_type_combo_ccs,
            PointDeCharge.prise_type_chademo,
            PointDeCharge.prise_type_autre,
            PointDeCharge.gratuit,
            PointDeCharge.paiement_acte,
            PointDeCharge.paiement_cb,
            PointDeCharge.paiement_autre,
            PointDeCharge.tarification,
            Station.condition_acces,
            PointDeCharge.reservation,
            Station.horaires,
            PointDeCharge.accessibilite_pmr,
            PointDeCharge.restriction_gabarit,
            Station.station_deux_roues,
            Station.raccordement,
            Station.num_pdl,
            Station.date_mise_en_service,
            PointDeCharge.observations,
            Station.date_maj,
            PointDeCharge.cable_t2_attache,
        )
        .select_from(PointDeCharge)
        .join(Station)
        .join(Amenageur)
        .join(Operateur)
        .join(Enseigne)
        .join(Localisation)
    )

    __table__ = create_materialized_view(
        name=STATIQUE_MV_TABLE_NAME,
        selectable=selectable,
        metadata=SQLModel.metadata,
        indexes=[
            Index("idx_statique_id_pdc_itinerance", "id_pdc_itinerance", unique=True),
            Index(
                "idx_statique_code_insee_commune",
                "code_insee_commune",
            ),
        ],
    )


mapper_registry.map_imperatively(StatiqueMV, _StatiqueMV.__table__)
