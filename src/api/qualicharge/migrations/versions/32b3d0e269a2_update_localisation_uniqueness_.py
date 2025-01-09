"""Update localisation uniqueness criterions

Revision ID: 32b3d0e269a2
Revises: c09664a85912
Create Date: 2025-01-09 16:20:52.578289

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "32b3d0e269a2"
down_revision: Union[str, None] = "c09664a85912"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "localisation_adresse_station_key", "localisation", type_="unique"
    )
    op.create_unique_constraint(
        "localisation_adresse_station_coordonneesXY_key",
        "localisation",
        ["adresse_station", "coordonneesXY"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "localisation_adresse_station_coordonneesXY_key", "localisation", type_="unique"
    )
    op.create_unique_constraint(
        "localisation_adresse_station_key", "localisation", ["adresse_station"]
    )
