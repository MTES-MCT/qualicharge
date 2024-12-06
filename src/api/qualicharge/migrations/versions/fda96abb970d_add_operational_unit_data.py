"""add operational unit data

Revision ID: fda96abb970d
Revises: 9d22385a3ae8
Create Date: 2024-05-15 16:08:19.687606

"""

from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import uuid4

from sqlalchemy import MetaData

from alembic import op

from qualicharge.fixtures.operational_units import data as operational_units
from qualicharge.schemas.core import OperationalUnitTypeEnum


# revision identifiers, used by Alembic.
revision: str = "fda96abb970d"
down_revision: Union[str, None] = "9d22385a3ae8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    data_upgrades()


def downgrade():
    data_downgrades()


def data_upgrades():
    """Add any optional data upgrade migrations here!"""
    # Reset table before inserting data
    data_downgrades()

    # Get OperationalUnit table
    metadata = MetaData()
    metadata.reflect(bind=op.get_bind())
    ou_table = metadata.tables["operationalunit"]

    # Bulk insert
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        ou_table,
        [
            {
                "id": uuid4().hex,
                "created_at": now,
                "updated_at": now,
                "type": "CHARGING",
            }
            | ou._asdict()
            for ou in operational_units
        ],
    )

    # Create FK
    op.execute(
        """
        WITH station_ou AS (
                SELECT
                  Station.id as station_id,
                  OperationalUnit.id as operational_unit_id
                FROM
                  Station
                  INNER JOIN OperationalUnit ON
                    SUBSTRING(Station.id_station_itinerance, 1, 5) = OperationalUnit.code
            )
            UPDATE Station
            SET operational_unit_id = station_ou.operational_unit_id
            FROM station_ou
            WHERE Station.id = station_ou.station_id
        """
    )


def data_downgrades():
    """Add any optional data downgrade migrations here!"""
    # Reset FK
    op.execute("UPDATE Station SET operational_unit_id = NULL")

    # Delete records
    op.execute("DELETE FROM OperationalUnit")
