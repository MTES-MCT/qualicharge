"""Add statique materialized view

Revision ID: 4b99d15436b0
Revises: 9ae109e209c9
Create Date: 2025-01-16 15:02:04.004411

"""

from typing import Sequence, Union

from alembic import op
from geoalchemy2.functions import ST_GeomFromEWKB
from sqlalchemy_utils.view import CreateView, DropView

from qualicharge.schemas.core import StatiqueMV, _StatiqueMV

# revision identifiers, used by Alembic.
revision: str = "4b99d15436b0"
down_revision: Union[str, None] = "9ae109e209c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the Statique Materialized view and related indexes."""
    op.execute(
        CreateView(
            _StatiqueMV.__table__.fullname, _StatiqueMV.selectable, materialized=True
        )
    )
    op.create_geospatial_index(
        "idx_statique_coordonneesXY",
        _StatiqueMV.__table__.fullname,
        [ST_GeomFromEWKB(StatiqueMV.coordonneesXY)],
        unique=False,
        postgresql_using="gist",
    )
    for idx in _StatiqueMV.__table__.indexes:
        idx.create(op.get_bind())


def downgrade() -> None:
    """Delete the Statique Materialized View."""

    op.execute(
        DropView(_StatiqueMV.__table__.fullname, materialized=True, cascade=True)
    )
