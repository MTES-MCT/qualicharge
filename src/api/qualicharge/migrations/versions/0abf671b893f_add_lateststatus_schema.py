"""add LatestStatus schema

Revision ID: 0abf671b893f
Revises: f2f66c7c092a
Create Date: 2025-06-26 12:52:32.809721

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0abf671b893f"
down_revision: Union[str, None] = "f2f66c7c092a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the lateststatus stable."""
    op.create_table(
        "lateststatus",
        sa.Column("horodatage", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "etat_pdc",
            postgresql.ENUM(
                "en_service",
                "hors_service",
                "inconnu",
                name="etat_pdc_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "occupation_pdc",
            postgresql.ENUM(
                "libre",
                "occupe",
                "reserve",
                "inconnu",
                name="occupation_pdc_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "etat_prise_type_2",
            postgresql.ENUM(
                "fonctionnel",
                "hors_service",
                "inconnu",
                name="etat_prise_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "etat_prise_type_combo_ccs",
            postgresql.ENUM(
                "fonctionnel",
                "hors_service",
                "inconnu",
                name="etat_prise_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "etat_prise_type_chademo",
            postgresql.ENUM(
                "fonctionnel",
                "hors_service",
                "inconnu",
                name="etat_prise_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "etat_prise_type_ef",
            postgresql.ENUM(
                "fonctionnel",
                "hors_service",
                "inconnu",
                name="etat_prise_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "id_pdc_itinerance", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("created_at <= updated_at", name="pre-creation-update"),
        sa.PrimaryKeyConstraint("id_pdc_itinerance"),
    )
    op.create_index(
        op.f("ix_lateststatus_horodatage"), "lateststatus", ["horodatage"], unique=False
    )


def downgrade() -> None:
    """Delete the lateststatus table and related indexes."""
    op.drop_index(op.f("ix_lateststatus_horodatage"), table_name="lateststatus")
    op.drop_table("lateststatus")
