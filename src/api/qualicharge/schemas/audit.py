"""QualiCharge auditable schemas."""

import logging
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import PastDatetime
from sqlalchemy import CheckConstraint, and_, event, insert, inspect
from sqlalchemy.orm import backref, foreign, relationship, remote
from sqlalchemy.types import JSON, DateTime
from sqlmodel import Field, SQLModel

logger = logging.getLogger(__name__)


class AuditableFieldBlackListEnum(StrEnum):
    """Fields black listed for auditability."""

    PASSWORD = "password"  # noqa: S105


class BaseAuditableSQLModel(SQLModel):
    """A base class for auditable SQL models.

    This class provides two timestamp fields, `created_at` and `updated_at`, which are
    automatically managed. The `created_at` field is set to the current UTC time when
    a new record is created, and the `updated_at` field is updated to the current UTC
    time whenever the record is modified.

    The two `created_by_id`, `updated_by_id` foreign keys points to the auth.User model.
    Both keys are optional and need to be explicitly set by your code.

    To fully track changes, you need to connect the `track_model_changes` utility (see
    below) to SQLAlchemy events.
    """

    __table_args__: Any = (
        CheckConstraint("created_at <= updated_at", name="pre-creation-update"),
    )

    created_at: PastDatetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp indicating when the record was created.",
    )  # type: ignore
    updated_at: PastDatetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp indicating when the record was last updated.",
    )  # type: ignore
    created_by_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    updated_by_id: Optional[UUID] = Field(default=None, foreign_key="user.id")


class Audit(SQLModel, table=True):
    """Model changes record for auditability."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    table: str
    author_id: UUID = Field(foreign_key="user.id")
    target_id: UUID
    updated_at: PastDatetime = Field(sa_type=DateTime(timezone=True))  # type: ignore
    changes: dict = Field(sa_type=JSON)


@event.listens_for(BaseAuditableSQLModel, "mapper_configured", propagate=True)
def add_audit_generic_fk(mapper, class_):
    """Create a generic foreign key to the Audit table for auditable schemas."""
    name = class_.__name__
    discriminator = name.lower()
    class_.audits = relationship(
        Audit,
        primaryjoin=and_(
            class_.id == foreign(remote(Audit.target_id)),
            Audit.table == discriminator,
        ),
        backref=backref(
            "target_%s" % discriminator,
            primaryjoin=remote(class_.id) == foreign(Audit.target_id),
        ),
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
            table=target.__tablename__,
            author_id=target.updated_by_id,
            target_id=target.id,
            updated_at=target.updated_at,
            changes=changes,
        )
    )
