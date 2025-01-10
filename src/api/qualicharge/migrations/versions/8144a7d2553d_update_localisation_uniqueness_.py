"""Update localisation uniqueness criterions

Revision ID: 8144a7d2553d
Revises: c09664a85912
Create Date: 2025-01-10 10:18:50.745037

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8144a7d2553d"
down_revision: Union[str, None] = "d3d2c20f8efd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "localisation_adresse_station_key", "localisation", type_="unique"
    )
    op.create_unique_constraint(
        "localisation_coordonneesXY_key", "localisation", ["coordonneesXY"]
    )


def downgrade() -> None:
    op.drop_constraint("localisation_coordonneesXY_key", "localisation", type_="unique")
    op.create_unique_constraint(
        "localisation_adresse_station_key", "localisation", ["adresse_station"]
    )
