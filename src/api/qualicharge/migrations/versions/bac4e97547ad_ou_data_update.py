"""Operational Units data update

Revision ID: bac4e97547ad
Revises: 5e801b64ce1c
Create Date: 2025-12-05 08:43:36.771267

"""

from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
from sqlalchemy import MetaData

from qualicharge.fixtures.operational_units import data as operational_units

# revision identifiers, used by Alembic.
revision: str = "bac4e97547ad"
down_revision: Union[str, None] = "5e801b64ce1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Legacy names
LEGACY = {}


# New operational units
NEW = {
    "FRALD",
    "FRALP",
    "FRHXW",
    "FRPRL",
    "FRRYM",
    "FRWPK",
}


def get_table():
    """Get operational units table."""
    # Get OperationalUnit table
    metadata = MetaData()
    metadata.reflect(bind=op.get_bind())
    return metadata.tables["operationalunit"]


def upgrade() -> None:
    """Create new entries and update existing ones."""
    ou_table = get_table()
    now = datetime.now(timezone.utc)

    # Bulk insert
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
            if ou.code in NEW
        ],
    )

    # Updates
    to_update = [ou for ou in operational_units if ou.code in LEGACY.keys()]
    for ou in to_update:
        op.execute(
            ou_table.update()
            .where(ou_table.c.code == op.inline_literal(ou.code))
            .values({"name": op.inline_literal(ou.name), "updated_at": now})
        )


def downgrade() -> None:
    """Remove new entries and restore legacy names."""
    ou_table = get_table()

    # Revert updates
    to_update = [ou for ou in operational_units if ou.code in LEGACY.keys()]
    for ou in to_update:
        op.execute(
            ou_table.update()
            .where(ou_table.c.code == op.inline_literal(ou.code))
            .values({"name": op.inline_literal(LEGACY[ou.code])})
        )

    # Delete new entries
    op.execute(ou_table.delete().where(ou_table.c.code.in_(NEW)))
