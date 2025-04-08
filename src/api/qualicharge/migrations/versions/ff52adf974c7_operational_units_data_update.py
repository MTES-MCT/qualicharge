"""Update operational units data

Revision ID: ff52adf974c7
Revises: 3eaef66b7629
Create Date: 2025-04-08 10:13:38.075909

"""

from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
from sqlalchemy import MetaData

from qualicharge.fixtures.operational_units import data as operational_units
from qualicharge.schemas.core import OperationalUnit

# revision identifiers, used by Alembic.
revision: str = "ff52adf974c7"
down_revision: Union[str, None] = "3eaef66b7629"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Legacy names
LEGACY = {
    "FRBLR": "MBLR",
}

# New operational units
NEW = {
    "FR151",
    "FRBE3",
    "FRCHF",
    "FRCHO",
    "FRDLM",
    "FRGLY",
    "FRHM1",
    "FRIMX",
    "FRITP",
    "FRQVI",
    "FRSPI",
    "FRYES",
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
