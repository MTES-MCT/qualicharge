"""Fix audit native_transaction_id type for postgresql-audit 0.18.

postgresql-audit 0.18.0 replaced `txid_current()` (bigint) with
`pg_current_xact_id()` (xid8) in its audit trigger templates, while the
`transaction` and `activity` tables created by 37189f57d370 declared
`native_transaction_id` as `bigint`. Recreate those columns as `xid8` so the
rebuilt triggers keep working.

Revision ID: e5c07a81d4b9
Revises: d3a491f0b2c7
Create Date: 2026-11-06 11:24:08.221314

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from postgresql_audit.base import versioning_manager
from sqlalchemy.orm import declarative_base
from sqlmodel import SQLModel

# revision identifiers, used by Alembic.
revision: str = "e5c07a81d4b9"
down_revision: Union[str, None] = "d3a491f0b2c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Table columns holding the native (PostgreSQL) transaction id.
NATIVE_TRANSACTION_ID_COLUMNS = [
    ("transaction", "native_transaction_id"),
    ("activity", "native_transaction_id"),
]


def get_column_type(table: str, column: str) -> str:
    """Return the SQL data type of the given column."""
    connection = op.get_bind()
    return connection.execute(
        sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "AND table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    ).scalar_one()


def recreate_audit_functions() -> None:
    """Re-create the audit functions from the installed postgresql-audit templates.

    Existing databases hold the legacy (postgresql-audit 0.17) `create_activity()`
    trigger function using `txid_current()`, which is incompatible with the
    `xid8` columns. Re-running the library listeners re-creates those functions
    (all templates use `CREATE OR REPLACE`).
    """
    versioning_manager.base = declarative_base(metadata=SQLModel.metadata)
    connection = op.get_bind()
    for table in versioning_manager.table_listeners:
        for _trig, event in versioning_manager.table_listeners[table]:
            if isinstance(event, sa.schema.DDL):
                op.execute(event)
            else:
                event("dummy_table_argument", connection)


def upgrade() -> None:
    """Alter audit native_transaction_id columns from bigint to xid8."""
    changed = False
    for table, column in NATIVE_TRANSACTION_ID_COLUMNS:
        if get_column_type(table, column) != "bigint":
            continue
        changed = True
        if table == "transaction":
            # xid8 has no gist operator class: drop the legacy exclusion
            # constraint before altering the column, then recreate it as a
            # unique constraint (as defined by postgresql-audit 0.18.0).
            op.drop_constraint("transaction_unique_native_tx_id", "transaction")
        op.execute(
            f'ALTER TABLE "{table}" '
            f'ALTER COLUMN "{column}" '
            f'TYPE xid8 USING "{column}"::text::xid8'
        )
        if table == "transaction":
            op.create_unique_constraint(
                "transaction_unique_native_tx_id", "transaction", [column]
            )
    if changed:
        recreate_audit_functions()


def downgrade() -> None:
    """Alter audit native_transaction_id columns from xid8 to bigint."""
    changed = False
    for table, column in NATIVE_TRANSACTION_ID_COLUMNS:
        if get_column_type(table, column) != "xid8":
            continue
        changed = True
        if table == "transaction":
            op.drop_constraint("transaction_unique_native_tx_id", "transaction")
        op.execute(
            f'ALTER TABLE "{table}" '
            f'ALTER COLUMN "{column}" '
            f'TYPE bigint USING "{column}"::text::bigint'
        )
        if table == "transaction":
            # NB: `op.create_exclude_constraint` cannot be used here: alembic
            # renders blank names for `text()` elements (ArgumentError).
            op.execute(
                'ALTER TABLE "transaction" '
                'ADD CONSTRAINT "transaction_unique_native_tx_id" '
                "EXCLUDE USING gist ("
                "native_transaction_id WITH =, "
                "tsrange(issued_at - INTERVAL '1 hour', issued_at) WITH &&)"
            )
    if changed:
        recreate_audit_functions()
