"""Add status and session missing indexes

Revision ID: f0f871ac556d
Revises: ff52adf974c7
Create Date: 2025-04-04 12:24:10.152681

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f0f871ac556d"
down_revision: Union[str, None] = "ff52adf974c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create session/status missing indexes."""
    # Status
    op.create_index("ix_status_pdc_id", "status", ["point_de_charge_id"])
    op.create_index("ix_status_horodatage", "status", ["horodatage"])
    op.create_index(
        "ix_status_horodatage_pdc_id", "status", ["horodatage", "point_de_charge_id"]
    )

    # Session
    op.create_index("ix_session_pdc_id", "session", ["point_de_charge_id"])
    op.create_index("ix_session_start", "session", ["start"])
    op.create_index(
        "ix_session_start_pdc_id", "session", ["start", "point_de_charge_id"]
    )


def downgrade() -> None:
    """Drop session/status indexes."""
    # Status
    op.drop_index("ix_status_pdc_id")
    op.drop_index("ix_status_horodatage")
    op.drop_index("ix_status_horodatage_pdc_id")

    # Session
    op.drop_index("ix_session_pdc_id")
    op.drop_index("ix_session_start")
    op.drop_index("ix_session_start_pdc_id")
