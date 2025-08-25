"""Alter db enum to varchar

Revision ID: 3e8ea07e5b66
Revises: 8144a7d2553d
Create Date: 2025-01-20 13:13:04.259534

"""

from enum import Enum, StrEnum
from typing import Any, Dict, List, Sequence, Type, Union

from sqlalchemy import Connection

from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import VARCHAR
from qualicharge.models.dynamic import EtatPDCEnum, EtatPriseEnum, OccupationPDCEnum

# revision identifiers, used by Alembic.
revision: str = "3e8ea07e5b66"
down_revision: Union[str, None] = "8144a7d2553d"
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
        "existing_enum_db_name": "implantationstationenum",
        "table_name": "station",
        "column_names": ["implantation_station"],
    },
    {
        "enum_": ConditionAccesEnum,
        "existing_enum_db_name": "conditionaccesenum",
        "table_name": "station",
        "column_names": ["condition_acces"],
    },
    {
        "enum_": RaccordementEnum,
        "existing_enum_db_name": "raccordementenum",
        "table_name": "station",
        "column_names": ["raccordement"],
    },
    {
        "enum_": AccessibilitePMREnum,
        "existing_enum_db_name": "accessibilitepmrenum",
        "table_name": "pointdecharge",
        "column_names": ["accessibilite_pmr"],
    },
    {
        "enum_": EtatPDCEnum,
        "existing_enum_db_name": "etatpdcenum",
        "table_name": "status",
        "column_names": ["etat_pdc"],
    },
    {
        "enum_": OccupationPDCEnum,
        "existing_enum_db_name": "occupationpdcenum",
        "table_name": "status",
        "column_names": ["occupation_pdc"],
    },
    {
        "enum_": EtatPriseEnum,
        "existing_enum_db_name": "etatpriseenum",
        "table_name": "status",
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
    existing_enum_db_name: str,
    table_name: str,
    column_names: List[str],
):
    """Upgrade database Enums from keys to VARCHAR."""
    print(f"Will upgrade {enum_.__name__} for table {table_name}")

    for column_name in column_names:
        print(f"{column_name=}")

        # Alter table column to a generic VARCHAR
        op.alter_column(
            table_name,
            column_name,
            existing_type=postgresql.ENUM(
                *enum_to_dict(enum_).keys(),
                name=existing_enum_db_name,
            ),
            type_=VARCHAR,
            existing_nullable=False,
            postgresql_using=f"{column_name}::VARCHAR",
        )

    # Delete the old ENUM database type
    postgresql.ENUM(
        *enum_to_dict(enum_).keys(),
        name=existing_enum_db_name,
    ).drop(connection, checkfirst=True)


def downgrade_db_enum(
    connection: Connection,
    enum_: Type[Enum],
    existing_enum_db_name: str,
    table_name: str,
    column_names: List[str],
):
    """Downgrade database Enums from VARCHAR to keys."""
    print(f"Will downgrade {enum_.__name__} for table {table_name}")

    # (re)create the old ENUM database type
    postgresql.ENUM(
        *enum_to_dict(enum_).keys(),
        name=existing_enum_db_name,
    ).create(connection, checkfirst=True)

    for column_name in column_names:
        print(f"{column_name=}")

        # Alter table column to a generic VARCHAR
        op.alter_column(
            table_name,
            column_name,
            existing_type=VARCHAR,
            type_=postgresql.ENUM(
                *enum_to_dict(enum_).keys(),
                name=existing_enum_db_name,
            ),
            existing_nullable=False,
            postgresql_using=f"{column_name}::{existing_enum_db_name}",
        )


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
