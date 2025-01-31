"""QualiCharge auditable schemas."""

import logging
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import PastDatetime
from sqlalchemy import and_, event, insert, inspect
from sqlalchemy.orm import backref, foreign, relationship, remote
from sqlalchemy.types import JSON, DateTime
from sqlalchemy_utils import generic_relationship
from sqlmodel import Field, SQLModel

from . import BaseTimestampedSQLModel

logger = logging.getLogger(__name__)


class AuditableFieldBlackListEnum(StrEnum):
    """Fields black listed for auditability."""

    PASSWORD = "password"  # noqa: S105


class BaseAuditableSQLModel(BaseTimestampedSQLModel):
    """A base class for auditable SQL models.

    The two `created_by_id`, `updated_by_id` foreign keys points to the auth.User model.
    Both keys are optional and need to be explicitly set by your code.

    To fully track changes, you need to connect the `track_model_changes` utility (see
    below) to SQLAlchemy events.
    """

    created_by_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    updated_by_id: Optional[UUID] = Field(default=None, foreign_key="user.id")


class Audit(SQLModel, table=True):
    """Model changes record for auditability."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    author_id: UUID = Field(foreign_key="user.id")
    target_table: str = Field(description="The table that we want to audit")
    target_id: UUID = Field(description="The table entry we are tracking changes from")
    updated_at: PastDatetime = Field(sa_type=DateTime(timezone=True))  # type: ignore
    changes: dict = Field(sa_type=JSON)

    _target = generic_relationship(target_table, target_id)


@event.listens_for(BaseAuditableSQLModel, "mapper_configured", propagate=True)
def add_audit_generic_fk(mapper, class_):
    """Create a generic foreign key to the Audit table for auditable schemas."""
    name = class_.__name__
    discriminator = name.lower()
    class_.audits = relationship(
        Audit,
        primaryjoin=and_(
            class_.id == foreign(remote(Audit.target_id)),
            Audit.target_table == discriminator,
        ),
        overlaps="audits"
    )

    @event.listens_for(class_.audits, "append")
    def append_audit(target, value, initiator):
        value.discriminator = discriminator


def track_model_changes(mapper, connection, target):
    """Track model changes for auditability.

    Models to track are supposed to inherit from the `BaseAuditableSQLModel`. You
    should listen to "after_update" events on your model to add full auditability
    support, e.g.:

    ```python
    from sqlalchemy import event

    from myapp.schemas import MyModel
    from ..schemas.audit import track_model_changes


    event.listen(MyModel, "after_update", track_model_changes)
    ```

    For each changed field, the previous value is stored along with the modification
    date and the author. For fields with sensitive information (_e.g._ passwords or
    tokens), a null value is stored.
    """
    if target.updated_by_id is None:
        logger.debug("Target updated_by_id is empty, aborting changes tracking.")
        return

    state = inspect(target)

    # Get changes
    changes = {}
    for attr in state.attrs:
        if attr.key in AuditableFieldBlackListEnum:
            continue
        history = attr.load_history()
        if not history.has_changes():
            continue
        changes[attr.key] = [
            str(history.deleted[0]) if len(history.deleted) else None,
            str(history.added[0]) if len(history.added) else None,
        ]

    logger.debug("Detected changes: %s", str(changes))

    # Log changes
    connection.execute(
        insert(Audit).values(
            author_id=target.updated_by_id,
            target_table=target.__tablename__,
            target_id=target.id,
            updated_at=target.updated_at,
            changes=changes,
        )
    )
