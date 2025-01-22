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
from sqlmodel import SQLModel

from qualicharge.schemas.core import PointDeCharge, Station, Status

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


def enum_to_dict(enum_: Type[Enum], revert: bool = False) -> Dict[str, Any]:
    """Convert enum to dict."""
    if revert:
        return {member.value: member.name for member in enum_}
    return {member.name: member.value for member in enum_}


def migrate_db_enum(
    connection: Connection,
    enum_: Type[Enum],
    existing_enum_db_name: str,
    new_enum_db_name: str,
    schema: SQLModel,
    column_names: List[str],
    revert: bool = False,
):
    """Migrate database Enum from keys to values (if revert if False).

    When revert is True, it migrates values to keys.
    """
    print(f"Will migrate {enum_.__name__} for table {schema.__tablename__} ({revert=})")

    # Create the new ENUM database type
    postgresql.ENUM(
        *enum_to_dict(enum_, revert).values(),
        name=new_enum_db_name,
    ).create(connection, checkfirst=True)

    for column_name in column_names:
        print(f"{column_name=}")

        # Alter table column to a generic VARCHAR
        op.alter_column(
            schema.__tablename__,
            column_name,
            existing_type=postgresql.ENUM(
                *enum_to_dict(enum_, revert).keys(),
                name=existing_enum_db_name,
            ),
            type_=VARCHAR,
            existing_nullable=False,
            postgresql_using=f"{column_name}::VARCHAR",
        )


def upgrade() -> None:
    # Alembic connection to the database
    connection = op.get_bind()

    fields_params = [
        {
            "enum_": ImplantationStationEnum,
            "existing_enum_db_name": "implantationstationenum",
            "new_enum_db_name": "implantation_station_enum",
            "schema": Station,
            "column_names": ["implantation_station"],
        },
        {
            "enum_": ConditionAccesEnum,
            "existing_enum_db_name": "conditionaccesenum",
            "new_enum_db_name": "condition_acces_enum",
            "schema": Station,
            "column_names": ["condition_acces"],
        },
        {
            "enum_": RaccordementEnum,
            "existing_enum_db_name": "raccordementenum",
            "new_enum_db_name": "raccordement_enum",
            "schema": Station,
            "column_names": ["raccordement"],
        },
        {
            "enum_": AccessibilitePMREnum,
            "existing_enum_db_name": "accessibilitepmrenum",
            "new_enum_db_name": "accessibilite_pmr_enum",
            "schema": PointDeCharge,
            "column_names": ["accessibilite_pmr"],
        },
        {
            "enum_": EtatPDCEnum,
            "existing_enum_db_name": "etatpdcenum",
            "new_enum_db_name": "etat_pdc_enum",
            "schema": Status,
            "column_names": ["etat_pdc"],
        },
        {
            "enum_": OccupationPDCEnum,
            "existing_enum_db_name": "occupationpdcenum",
            "new_enum_db_name": "occupation_pdc_enum",
            "schema": Status,
            "column_names": ["occupation_pdc"],
        },
        {
            "enum_": EtatPriseEnum,
            "existing_enum_db_name": "etatpriseenum",
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
    for field_params in fields_params:
        migrate_db_enum(connection, **field_params)


def downgrade() -> None:
    # Alembic connection to the database
    connection = op.get_bind()

    fields_params = [
        {
            "enum_": ImplantationStationEnum,
            "existing_enum_db_name": "implantation_station_enum",
            "new_enum_db_name": "implantationstationenum",
            "schema": Station,
            "column_names": ["implantation_station"],
        },
        {
            "enum_": ConditionAccesEnum,
            "existing_enum_db_name": "condition_acces_enum",
            "new_enum_db_name": "conditionaccesenum",
            "schema": Station,
            "column_names": ["condition_acces"],
        },
        {
            "enum_": RaccordementEnum,
            "existing_enum_db_name": "raccordement_enum",
            "new_enum_db_name": "raccordementenum",
            "schema": Station,
            "column_names": ["raccordement"],
        },
        {
            "enum_": AccessibilitePMREnum,
            "existing_enum_db_name": "accessibilite_pmr_enum",
            "new_enum_db_name": "accessibilitepmrenum",
            "schema": PointDeCharge,
            "column_names": ["accessibilite_pmr"],
        },
        {
            "enum_": EtatPDCEnum,
            "existing_enum_db_name": "etat_pdc_enum",
            "new_enum_db_name": "etatpdcenum",
            "schema": Status,
            "column_names": ["etat_pdc"],
        },
        {
            "enum_": OccupationPDCEnum,
            "existing_enum_db_name": "occupation_pdc_enum",
            "new_enum_db_name": "occupationpdcenum",
            "schema": Status,
            "column_names": ["occupation_pdc"],
        },
        {
            "enum_": EtatPriseEnum,
            "existing_enum_db_name": "etat_prise_enum",
            "new_enum_db_name": "etatpriseenum",
            "schema": Status,
            "column_names": [
                "etat_prise_type_2",
                "etat_prise_type_combo_ccs",
                "etat_prise_type_chademo",
                "etat_prise_type_ef",
            ],
        },
    ]
    for field_params in fields_params:
        migrate_db_enum(connection, **field_params, revert=True)
