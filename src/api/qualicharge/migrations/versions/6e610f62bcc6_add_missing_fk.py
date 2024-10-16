"""add missing fk

Revision ID: 6e610f62bcc6
Revises: b69ed697b446
Create Date: 2024-10-16 15:44:28.265424

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6e610f62bcc6"
down_revision: Union[str, None] = "b69ed697b446"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create missing PKs
    op.create_primary_key("region_pkey", "region", ["id"])
    op.create_primary_key("department_pkey", "department", ["id"])
    op.create_primary_key("epci_pkey", "epci", ["id"])
    op.create_primary_key("city_pkey", "city", ["id"])

    # And FKs
    op.create_foreign_key(
        "city_department_id_fkey", "city", "department", ["department_id"], ["id"]
    )
    op.create_foreign_key("city_epci_id_fkey", "city", "epci", ["epci_id"], ["id"])
    op.create_foreign_key(
        "department_region_id_fkey", "department", "region", ["region_id"], ["id"]
    )


def downgrade() -> None:
    # Delete PKs
    op.drop_constraint("region_pkey", "region", type_="primary")
    op.drop_constraint("department_pkey", "department", type_="primary")
    op.drop_constraint("epci_pkey", "epci", type_="primary")
    op.drop_constraint("city_pkey", "city", type_="primary")

    # Delete FKs
    op.drop_constraint("department_region_id_fkey", "department", type_="foreignkey")
    op.drop_constraint("city_epci_id_fkey", "city", type_="foreignkey")
    op.drop_constraint("city_department_id_fkey", "city", type_="foreignkey")
