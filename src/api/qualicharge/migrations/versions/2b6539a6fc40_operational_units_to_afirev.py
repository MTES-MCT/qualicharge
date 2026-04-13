"""Operational units to AFIREV data model.

Revision ID: 2b6539a6fc40
Revises: 61de84df9030
Create Date: 2026-04-24 12:51:48.818868

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2b6539a6fc40"
down_revision: Union[str, None] = "61de84df9030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update the OperationalUnit model to stick with AFIREV data model."""
    connection = op.get_bind()

    # Update enums
    op.execute("ALTER TYPE operationalunittypeenum ADD VALUE 'BOTH'")

    # Create new enum
    postgresql.ENUM(
        "ACTIVE",
        "AWAITING_PAYMENT",
        "INACTIVE",
        "SUSPENDED",
        name="operationalunitstatusenum",
    ).create(connection, checkfirst=True)

    # Add columns
    op.add_column(
        "operationalunit",
        sa.Column("amenageur", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "operationalunit",
        sa.Column("exploitant", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "operationalunit",
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "AWAITING_PAYMENT",
                "INACTIVE",
                "SUSPENDED",
                name="operationalunitstatusenum",
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Rollback to the previous OperationalUnit model."""
    connection = op.get_bind()

    # Remove columns
    op.drop_column("operationalunit", "status")
    op.drop_column("operationalunit", "exploitant")
    op.drop_column("operationalunit", "amenageur")

    # Delete enum
    postgresql.ENUM(
        "ACTIVE",
        "AWAITING_PAYMENT",
        "INACTIVE",
        "SUSPENDED",
        name="operationalunitstatusenum",
    ).drop(connection, checkfirst=True)

    # -- Rollback enum
    # Re-create the old enum with a temporary name and assign it to the type column
    postgresql.ENUM(
        "CHARGING",
        "MOBILITY",
        name="tmp_operationalunittypeenum",
    ).create(connection, checkfirst=True)
    op.alter_column(
        "operationalunit",
        "type",
        existing_type=postgresql.ENUM(
            "BOTH" "CHARGING",
            "MOBILITY",
            name="operationalunittypeenum",
        ),
        type_=postgresql.ENUM(
            "CHARGING",
            "MOBILITY",
            name="tmp_operationalunittypeenum",
        ),
        existing_nullable=False,
        postgresql_using="type::VARCHAR::tmp_operationalunittypeenum",
    )

    # Delete the new enum
    postgresql.ENUM(
        "CHARGING",
        "MOBILITY",
        "BOTH",
        name="operationalunittypeenum",
    ).drop(connection, checkfirst=True)

    # Rename the old enum as expected
    op.execute(
        "ALTER TYPE tmp_operationalunittypeenum RENAME TO operationalunittypeenum"
    )
