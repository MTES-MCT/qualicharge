"""Rename PointDeCharge and Station views

Revision ID: b4c72cbe1932
Revises: b8a68ed35a6f
Create Date: 2025-08-26 15:42:49.285245

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4c72cbe1932"
down_revision: Union[str, None] = "b8a68ed35a6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename PointDeCharge and Station view to lower case."""
    op.execute('ALTER VIEW IF EXISTS "PointDeCharge" rename to pointdecharge')
    op.execute('ALTER VIEW IF EXISTS "Station" rename to station')


def downgrade() -> None:
    """Rename pointdecharge and station view to camel case."""
    op.execute('ALTER VIEW IF EXISTS pointdecharge rename to "PointDeCharge"')
    op.execute('ALTER VIEW IF EXISTS station rename to "Station"')
