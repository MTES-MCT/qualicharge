"""add soft delete to pointdecharge and station

Revision ID: 80d63e775b17
Revises: 0abf671b893f
Create Date: 2025-07-02 14:40:55.228614

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "80d63e775b17"
down_revision: Union[str, None] = "0abf671b893f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create PointDeCharge and Station table soft-delete fields."""
    op.add_column(
        "pointdecharge",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("pointdecharge", sa.Column("deleted_by_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "pointdecharge_deleted_by_id_fk",
        "pointdecharge",
        "user",
        ["deleted_by_id"],
        ["id"],
    )
    op.add_column(
        "station", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("station", sa.Column("deleted_by_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "station_deleted_by_id_fk", "station", "user", ["deleted_by_id"], ["id"]
    )


def downgrade() -> None:
    """Delete PointDeCharge and Station table soft-delete fields."""
    op.drop_constraint("station_deleted_by_id_fk", "station", type_="foreignkey")
    op.drop_column("station", "deleted_by_id")
    op.drop_column("station", "deleted_at")
    op.drop_constraint(
        "pointdecharge_deleted_by_id_fk", "pointdecharge", type_="foreignkey"
    )
    op.drop_column("pointdecharge", "deleted_by_id")
    op.drop_column("pointdecharge", "deleted_at")
