"""statique raccordement null to direct

Revision ID: 61de84df9030
Revises: bac4e97547ad
Create Date: 2026-02-28 12:56:40.900142

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import MetaData

from qualicharge.models.static import RaccordementEnum

# revision identifiers, used by Alembic.
revision: str = "61de84df9030"
down_revision: Union[str, None] = "bac4e97547ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate NULL Station.raccordement field values to 'Direct'."""
    # Get Station table
    metadata = MetaData()
    metadata.reflect(bind=op.get_bind())
    table = metadata.tables["_station"]

    op.execute(
        table.update()
        .where(table.c.raccordement == None)
        .values(raccordement=RaccordementEnum.DIRECT)
    )


def downgrade() -> None:
    """Do nothing. We cannot revert the current migration."""
