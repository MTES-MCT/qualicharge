"""Operational Units data update

Revision ID: cefaa3fcc0d4
Revises: b4c72cbe1932
Create Date: 2025-08-27 09:35:35.427807

"""

from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
from sqlalchemy import MetaData

from qualicharge.fixtures.operational_units import data as operational_units

# revision identifiers, used by Alembic.
revision: str = "cefaa3fcc0d4"
down_revision: Union[str, None] = "b4c72cbe1932"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New operational units
NEW = {
    "FRAU1",
    "FRLEA",
    "FRMB1",
    "FRMNA",
    "FRMOT",
    "FRPLN",
    "FRRE1",
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


def downgrade() -> None:
    """Remove new entries and restore legacy names."""
    ou_table = get_table()

    # Delete new entries
    op.execute(ou_table.delete().where(ou_table.c.code.in_(NEW)))
