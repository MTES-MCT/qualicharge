"""add user old_password field

Revision ID: 2e2b728b6298
Revises: c587b03fe0b4
Create Date: 2026-10-11 17:44:10.342224

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "2e2b728b6298"
down_revision: Union[str, None] = "c587b03fe0b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user old password-related columns."""
    op.add_column(
        "user",
        sa.Column(
            "old_password", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=True
        ),
    )
    op.add_column(
        "user",
        sa.Column("old_password_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Drop user old password-related columns."""
    op.drop_column("user", "old_password_expires_at")
    op.drop_column("user", "old_password")
