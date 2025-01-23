"""Update db enum values and type

Revision ID: 9ae109e209c9
Revises: 3e8ea07e5b66
Create Date: 2025-01-23 09:30:16.055204

"""

from enum import Enum, StrEnum
from typing import Any, Dict, List, Sequence, Type, Union

from sqlalchemy import Connection

from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import VARCHAR
from qualicharge.models.dynamic import EtatPDCEnum, EtatPriseEnum, OccupationPDCEnum
from sqlmodel import Session, SQLModel, update

from qualicharge.schemas.core import PointDeCharge, Station, Status

# revision identifiers, used by Alembic.
revision: str = "9ae109e209c9"
down_revision: Union[str, None] = "3e8ea07e5b66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class ImplantationStationEnum(StrEnum):
    """Statique.implantation_station field enum."""

    VOIRIE = "Voirie"
    PARKING_PUBLIC = "Parking public"
    PARKING_PRIVE_USAGE_PUBLIC = "Parking privé à usage public"
    PARKING_PRIVE_CLIENTELE = "Parking privé réservé à la clientèle"
    STATION_RECHARGE_RAPIDE = "Station dédiée à la recharge rapide"


class ConditionAccesEnum(StrEnum):
    """Statique.condition_acces field enum."""

    ACCESS_LIBRE = "Accès libre"
    ACCESS_RESERVE = "Accès réservé"


class AccessibilitePMREnum(StrEnum):
    """Statique.accessibilite_pmr field enum."""

    RESERVE_PMR = "Réservé PMR"
    NON_RESERVE = "Accessible mais non réservé PMR"
    NON_ACCESSIBLE = "Non accessible"
    INCONNUE = "Accessibilité inconnue"


class RaccordementEnum(StrEnum):
    """Statique.raccordement field enum."""

    DIRECT = "Direct"
    INDIRECT = "Indirect"


def enum_to_dict(enum_: Type[Enum]) -> Dict[str, Any]:
    """Convert enum to dict."""
    return {member.name: member.value for member in enum_}


FIELDS_PARAMS = [
    {
        "enum_": ImplantationStationEnum,
        "new_enum_db_name": "implantation_station_enum",
        "schema": Station,
        "column_names": ["implantation_station"],
    },
    {
        "enum_": ConditionAccesEnum,
        "new_enum_db_name": "condition_acces_enum",
        "schema": Station,
        "column_names": ["condition_acces"],
    },
    {
        "enum_": RaccordementEnum,
        "new_enum_db_name": "raccordement_enum",
        "schema": Station,
        "column_names": ["raccordement"],
    },
    {
        "enum_": AccessibilitePMREnum,
        "new_enum_db_name": "accessibilite_pmr_enum",
        "schema": PointDeCharge,
        "column_names": ["accessibilite_pmr"],
    },
    {
        "enum_": EtatPDCEnum,
        "new_enum_db_name": "etat_pdc_enum",
        "schema": Status,
        "column_names": ["etat_pdc"],
    },
    {
        "enum_": OccupationPDCEnum,
        "new_enum_db_name": "occupation_pdc_enum",
        "schema": Status,
        "column_names": ["occupation_pdc"],
    },
    {
        "enum_": EtatPriseEnum,
        "new_enum_db_name": "etat_prise_enum",
        "schema": Status,
        "column_names": [
            "etat_prise_type_2",
            "etat_prise_type_combo_ccs",
            "etat_prise_type_chademo",
            "etat_prise_type_ef",
        ],
    },
]


def upgrade_db_enum(
    connection: Connection,
    enum_: Type[Enum],
    new_enum_db_name: str,
    schema: SQLModel,
    column_names: List[str],
):
    """Upgrade database Enums from VARCHAR to values."""
    print(f"Will upgrade {enum_.__name__} for table {schema.__tablename__}")

    # Create the new ENUM database type
    postgresql.ENUM(
        *enum_to_dict(enum_).values(),
        name=new_enum_db_name,
    ).create(connection, checkfirst=True)

    for column_name in column_names:
        print(f"{column_name=}")

        # Update data
        with Session(connection) as session:
            for key, value in enum_to_dict(enum_).items():
                session.exec(
                    update(schema)
                    .where(getattr(schema, column_name) == key)
                    .values({column_name: value})
                )

        # Alter table column to a the new ENUM
        op.alter_column(
            schema.__tablename__,
            column_name,
            existing_type=VARCHAR,
            type_=postgresql.ENUM(
                *enum_to_dict(enum_).values(),
                name=new_enum_db_name,
            ),
            existing_nullable=False,
            postgresql_using=f"{column_name}::{new_enum_db_name}",
        )


def downgrade_db_enum(
    connection: Connection,
    enum_: Type[Enum],
    new_enum_db_name: str,
    schema: SQLModel,
    column_names: List[str],
):
    """Downgrade database Enums from VARCHAR to values."""
    print(f"Will downgrade {enum_.__name__} for table {schema.__tablename__}")

    for column_name in column_names:
        print(f"{column_name=}")

        # Alter table column to a VARCHAR
        op.alter_column(
            schema.__tablename__,
            column_name,
            existing_type=postgresql.ENUM(
                *enum_to_dict(enum_).values(),
                name=new_enum_db_name,
            ),
            type_=VARCHAR,
            existing_nullable=False,
            postgresql_using=f"{column_name}::{new_enum_db_name}",
        )

        # Update data
        with Session(connection) as session:
            for key, value in enum_to_dict(enum_).items():
                session.exec(
                    update(schema)
                    .where(getattr(schema, column_name) == value)
                    .values({column_name: key})
                )

    # Delete new ENUM database type
    postgresql.ENUM(
        *enum_to_dict(enum_).values(),
        name=new_enum_db_name,
    ).drop(connection, checkfirst=True)


def upgrade() -> None:
    # Alembic connection to the database
    connection = op.get_bind()
    for field_params in FIELDS_PARAMS:
        upgrade_db_enum(connection, **field_params)


def downgrade() -> None:
    # Alembic connection to the database
    connection = op.get_bind()
    for field_params in FIELDS_PARAMS:
        downgrade_db_enum(connection, **field_params)
