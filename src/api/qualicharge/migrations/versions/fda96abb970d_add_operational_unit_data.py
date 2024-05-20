"""add operational unit data

Revision ID: fda96abb970d
Revises: 9d22385a3ae8
Create Date: 2024-05-15 16:08:19.687606

"""

from typing import Sequence, Union

from alembic import op
from sqlmodel import Session, select

from qualicharge.fixtures.operational_units import operational_units
from qualicharge.schemas import Station


# revision identifiers, used by Alembic.
revision: str = "fda96abb970d"
down_revision: Union[str, None] = "9d22385a3ae8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    data_upgrades()


def downgrade():
    data_downgrades()


def data_upgrades():
    """Add any optional data upgrade migrations here!"""

    # We are running in a transaction, hence we need to get the current active connection
    session = Session(op.get_bind())

    # Reset table before inserting data
    data_downgrades()
    session.add_all(operational_units)
    session.commit()

    # Create FK
    for operational_unit in operational_units:
        operational_unit.create_stations_fk(session)


def data_downgrades():
    """Add any optional data downgrade migrations here!"""

    # We are running in a transaction, hence we need to get the current active connection
    session = Session(op.get_bind())

    # Reset FK
    stations = session.exec(select(Station)).all()
    for station in stations:
        station.operational_unit_id = None
    session.add_all(stations)
    session.commit()

    # Delete records
    op.execute("delete from operationalunit")
