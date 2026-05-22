"""store original tariff raw payload.

Revision ID: 2cb4b3c9d4e8
Revises: c587b03fe0b4
Create Date: 2026-05-22 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2cb4b3c9d4e8"
down_revision: Union[str, None] = "c587b03fe0b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add original tariff raw payload storage."""
    jsonb_type = postgresql.JSONB(astext_type=sa.Text())
    op.add_column(
        "tariff",
        sa.Column("original_raw", jsonb_type, nullable=True),
    )
    op.execute("UPDATE tariff SET original_raw = raw WHERE original_raw IS NULL")
    op.alter_column(
        "tariff",
        "original_raw",
        existing_type=jsonb_type,
        nullable=False,
    )


def downgrade() -> None:
    """Remove original tariff raw payload storage."""
    op.drop_column("tariff", "original_raw")
