"""Fix session hypertable creation

Revision ID: d7425ed47afd
Revises: 2d5ecaec5672
Create Date: 2025-04-16 15:34:20.392315

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7425ed47afd"
down_revision: Union[str, None] = "2d5ecaec5672"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create session hypertable and related indexes."""
    op.drop_constraint("session_pkey", "session")
    op.drop_index("ix_session_start")
    op.create_index("ix_session_id_start", "session", ["id", "start"], unique=True)
    op.execute(
        "SELECT create_hypertable('session', by_range('start'), migrate_data => TRUE);"
    )


def downgrade() -> None:
    """Restore Session to a standard postgres table."""
    # Duplicate table structure
    op.execute("CREATE TABLE pg_session (LIKE session INCLUDING ALL)")
    # Copy all data
    op.execute("INSERT INTO pg_session (SELECT * FROM session)")
    # Drop the hypertable
    op.drop_table("session")
    # Rename regular table
    op.rename_table("pg_session", "session")
    op.create_primary_key("session_pkey", "session", ["id"])
    op.create_index("ix_session_start", "session", ["start"])
