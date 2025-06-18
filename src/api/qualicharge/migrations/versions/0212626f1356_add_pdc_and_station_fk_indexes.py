"""add PDC and station fk indexes

Revision ID: 0212626f1356
Revises: b0bcee4ed64a
Create Date: 2025-06-18 14:41:35.673730

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0212626f1356"
down_revision: Union[str, None] = "b0bcee4ed64a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create PDC and station FK indexes."""
    op.create_index(
        op.f("ix_pointdecharge_station_id"),
        "pointdecharge",
        ["station_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_station_amenageur_id"), "station", ["amenageur_id"], unique=False
    )
    op.create_index(
        op.f("ix_station_operateur_id"), "station", ["operateur_id"], unique=False
    )


def downgrade() -> None:
    """Drop PDC and station FK indexes."""
    op.drop_index(op.f("ix_station_operateur_id"), table_name="station")
    op.drop_index(op.f("ix_station_amenageur_id"), table_name="station")
    op.drop_index(op.f("ix_pointdecharge_station_id"), table_name="pointdecharge")
