"""Fix statique MV spatial index.

Replace the legacy functional GIST index over `st_geomfromewkb(coordonneesXY)`
with a plain column GIST index. GeoAlchemy2 0.20.0 no longer supports compiling
such functional index expressions (see 4b99d15436b0 and b8a68ed35a6f fixes).

Revision ID: d3a491f0b2c7
Revises: 2e2b728b6298
Create Date: 2026-11-06 10:12:33.145721

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3a491f0b2c7"
down_revision: Union[str, None] = "2e2b728b6298"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Recreate the Statique MV spatial index as a plain column GIST index."""
    op.drop_index("idx_statique_coordonneesXY", table_name="statique")
    op.create_index(
        "idx_statique_coordonneesXY",
        "statique",
        ["coordonneesXY"],
        unique=False,
        postgresql_using="gist",
    )


def downgrade() -> None:
    """Restore the legacy functional GIST index."""
    op.drop_index("idx_statique_coordonneesXY", table_name="statique")
    op.execute(
        "CREATE INDEX idx_statique_coordonneesXY "
        "ON statique USING gist (st_geomfromewkb(coordonneesXY))"
    )
