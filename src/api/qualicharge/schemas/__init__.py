"""QualiCharge schemas."""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import PastDatetime
from sqlalchemy import CheckConstraint
from sqlalchemy.types import DateTime
from sqlmodel import Field, SQLModel


class BaseTimestampedSQLModel(SQLModel):
    """A base class for SQL models with timestamp fields.

    This class provides two timestamp fields, `created_at` and `updated_at`, which are
    automatically managed. The `created_at` field is set to the current UTC time when
    a new record is created, and the `updated_at` field is updated to the current UTC
    time whenever the record is modified.
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


class BaseAuditableSQLModel(BaseTimestampedSQLModel):
    """A base class for SQL models for which we track changes making them auditable."""

    __versioned__ = {"exclude": ["created_at", "updated_at"]}

    created_by_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    updated_by_id: Optional[UUID] = Field(default=None, foreign_key="user.id")


class SoftDeleteMixin:
    """A mixin to enable table soft-delete."""

    deleted_at: Optional[PastDatetime] = Field(
        sa_type=DateTime(timezone=True),
        default=None,
        description="The timestamp indicating when the record was soft-deleted.",
    )  # type: ignore
    deleted_by_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
