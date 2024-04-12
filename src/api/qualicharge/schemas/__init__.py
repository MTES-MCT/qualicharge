"""QualiCharge schemas."""

from datetime import datetime, timezone
from typing import Tuple

from pydantic.types import PastDatetime
from sqlalchemy import CheckConstraint, Constraint
from sqlalchemy.types import DateTime
from sqlmodel import Field, SQLModel


class BaseTimestampedSQLModel(SQLModel):
    """A base class for SQL models with timestamp fields.

    This class provides two timestamp fields, `created_at` and `updated_at`, which are
    automatically managed. The `created_at` field is set to the current UTC time when
    a new record is created, and the `updated_at` field is updated to the current UTC
    time whenever the record is modified.
    """

    __table_args__: Tuple[Constraint, ...] = (
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
