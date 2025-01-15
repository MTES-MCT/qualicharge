"""Update Enum definitions

Revision ID: d3d2c20f8efd
Revises: c09664a85912
Create Date: 2025-01-15 16:13:18.986021

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d3d2c20f8efd"
down_revision: Union[str, None] = "c09664a85912"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create expected ENUM
    postgresql.ENUM("DIRECT", "INDIRECT", name="raccordementenum").create(
        op.get_bind(), checkfirst=True
    )

    # Update column type
    op.alter_column(
        "station",
        "raccordement",
        existing_type=postgresql.ENUM("DIRECT", "INDIRECT", name="raccordementemum"),
        type_=postgresql.ENUM("DIRECT", "INDIRECT", name="raccordementenum"),
        existing_nullable=True,
        postgresql_using="raccordement::VARCHAR::raccordementenum",
    )

    # Delete old enum
    postgresql.ENUM("DIRECT", "INDIRECT", name="raccordementemum").drop(
        op.get_bind(), checkfirst=True
    )


def downgrade() -> None:
    # Create old ENUM
    postgresql.ENUM("DIRECT", "INDIRECT", name="raccordementemum").create(
        op.get_bind(), checkfirst=True
    )

    # Rollback changes
    op.alter_column(
        "station",
        "raccordement",
        existing_type=postgresql.ENUM("DIRECT", "INDIRECT", name="raccordementenum"),
        type_=postgresql.ENUM("DIRECT", "INDIRECT", name="raccordementemum"),
        existing_nullable=True,
        postgresql_using="raccordement::VARCHAR::raccordementemum",
    )

    # Delete created enum
    postgresql.ENUM("DIRECT", "INDIRECT", name="raccordementenum").drop(
        op.get_bind(), checkfirst=True
    )
