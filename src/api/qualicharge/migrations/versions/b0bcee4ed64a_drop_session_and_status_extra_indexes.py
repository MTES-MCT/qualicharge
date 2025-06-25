"""Drop session and status extra indexes

Revision ID: b0bcee4ed64a
Revises: 1270d547e358
Create Date: 2025-06-18 14:04:55.846763

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b0bcee4ed64a"
down_revision: Union[str, None] = "1270d547e358"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove extra indexes."""
    op.drop_index("ix_session_start_pdc_id", table_name="session")
    op.drop_index("session_start_idx", table_name="session")
    op.drop_index("ix_status_horodatage_pdc_id", table_name="status")
    op.drop_index("status_horodatage_idx", table_name="status")


def downgrade() -> None:
    """Restore extra indexes."""
    op.create_index(
        "status_horodatage_idx",
        "status",
        [sa.literal_column("horodatage DESC")],
        unique=False,
    )
    op.create_index(
        "ix_status_horodatage_pdc_id",
        "status",
        ["horodatage", "point_de_charge_id"],
        unique=False,
    )
    op.create_index(
        "session_start_idx", "session", [sa.literal_column("start DESC")], unique=False
    )
    op.create_index(
        "ix_session_start_pdc_id",
        "session",
        ["start", "point_de_charge_id"],
        unique=False,
    )
