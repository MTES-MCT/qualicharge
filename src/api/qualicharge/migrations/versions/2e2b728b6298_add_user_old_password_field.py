"""Add user old_password field.

Revision ID: 2e2b728b6298
Revises: c587b03fe0b4
Create Date: 2026-10-11 17:44:10.342224

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from postgresql_audit.base import versioning_manager

# revision identifiers, used by Alembic.
revision: str = "2e2b728b6298"
down_revision: Union[str, None] = "c587b03fe0b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Exclusion list prior to this revision (without old_password).
USER_AUDIT_LEGACY_EXCLUDED_COLUMNS = [
    "created_at",
    "updated_at",
    "password",
]
# Columns excluded from the audit trail: timestamps are managed by the ORM and
# password hashes must not leak into activity old_data/changed_data.
USER_AUDIT_EXCLUDED_COLUMNS = [
    *USER_AUDIT_LEGACY_EXCLUDED_COLUMNS,
    "old_password",
]


def rebuild_user_audit_trigger(legacy: bool = False) -> None:
    """Rebuild the user table audit trigger."""
    metadata = sa.MetaData()
    metadata.reflect(bind=op.get_bind(), only=("user",))
    table = metadata.tables["user"]
    op.execute(
        versioning_manager.build_audit_table_query(
            table=table,
            exclude_columns=(
                USER_AUDIT_LEGACY_EXCLUDED_COLUMNS
                if legacy
                else USER_AUDIT_EXCLUDED_COLUMNS
            ),
        )
    )


def upgrade() -> None:
    """Add user old password-related columns."""
    op.add_column(
        "user",
        sa.Column(
            "old_password", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=True
        ),
    )
    op.add_column(
        "user",
        sa.Column("old_password_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Refresh the audit trigger so that old_password hashes are excluded from
    # the activity trail.
    rebuild_user_audit_trigger()


def downgrade() -> None:
    """Drop user old password-related columns."""
    rebuild_user_audit_trigger(legacy=True)
    op.drop_column("user", "old_password_expires_at")
    op.drop_column("user", "old_password")
