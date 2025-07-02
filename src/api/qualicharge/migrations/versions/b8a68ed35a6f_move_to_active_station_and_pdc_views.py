"""Move to active station and pdc views

Revision ID: b8a68ed35a6f
Revises: 80d63e775b17
Create Date: 2025-07-17 16:41:18.638295

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.view import CreateView, DropView

from geoalchemy2.functions import ST_GeomFromEWKB
from qualicharge.schemas.core import (
    ActivePointsDeChargeView,
    ActiveStationsView,
    StatiqueMV,
    _StatiqueMV,
)

# revision identifiers, used by Alembic.
revision: str = "b8a68ed35a6f"
down_revision: Union[str, None] = "80d63e775b17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add soft-delete for station and pointdecharge.

    1. Rename Station and PointDeCharge tables.
    2. Create ActiveStation and ActivePointDeCharge views.
    3. Update Statique materialized view
    """
    op.rename_table("station", "_station")
    op.rename_table("pointdecharge", "_pointdecharge")
    op.execute(
        CreateView(
            ActiveStationsView.__table__.fullname,
            ActiveStationsView.selectable,
            materialized=False,
        )
    )
    op.execute(
        CreateView(
            ActivePointsDeChargeView.__table__.fullname,
            ActivePointsDeChargeView.selectable,
            materialized=False,
        )
    )

    # Drop and re-create the Statique materialized view to use only active entities
    op.execute(
        DropView(_StatiqueMV.__table__.fullname, materialized=True, cascade=True)
    )
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
    """Rollback soft-delete for station and pointdecharge."""
    op.execute(
        DropView(
            ActivePointsDeChargeView.__table__.fullname,
            materialized=False,
            cascade=True,
        )
    )
    op.execute(
        DropView(
            ActiveStationsView.__table__.fullname, materialized=False, cascade=True
        )
    )
    op.rename_table("_pointdecharge", "pointdecharge")
    op.rename_table("_station", "station")

    # Drop and re-create the Statique materialized view to use only active entities
    op.execute(
        DropView(_StatiqueMV.__table__.fullname, materialized=True, cascade=True)
    )
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
