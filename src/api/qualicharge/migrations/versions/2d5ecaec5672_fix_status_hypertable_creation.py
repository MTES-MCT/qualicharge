"""Fix status hypertable creation

Revision ID: 2d5ecaec5672
Revises: f0f871ac556d
Create Date: 2025-04-15 16:56:14.774236

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2d5ecaec5672"
down_revision: Union[str, None] = "f0f871ac556d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create status hypertable and related indexes."""
    op.drop_constraint("status_pkey", "status")
    op.drop_index("ix_status_horodatage")
    op.create_index(
        "ix_status_id_horodatage", "status", ["id", "horodatage"], unique=True
    )
    op.execute(
        "SELECT create_hypertable('status', by_range('horodatage'), migrate_data => TRUE);"
    )


def downgrade() -> None:
    """Restore Status to a standard postgres table."""
    # Duplicate table structure
    op.execute("CREATE TABLE pg_status (LIKE status INCLUDING ALL)")
    # Copy all data
    op.execute("INSERT INTO pg_status (SELECT * FROM status)")
    # Drop the hypertable
    op.drop_table("status")
    # Rename regular table
    op.rename_table("pg_status", "status")
    op.create_primary_key("status_pkey", "status", ["id"])
    op.create_index("ix_status_horodatage", "status", ["horodatage"])
