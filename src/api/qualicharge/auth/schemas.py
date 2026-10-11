"""QualiCharge authentication schemas."""

import logging
from datetime import datetime, timezone
from enum import StrEnum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import EmailStr, FutureDatetime, PastDatetime
from sqlalchemy.types import ARRAY, DateTime, String
from sqlmodel import Field, Relationship, SQLModel

from qualicharge.conf import settings
from qualicharge.schemas import BaseAuditableSQLModel
from qualicharge.schemas.core import OperationalUnit

logger = logging.getLogger(__name__)


# -- Many-to-many relationships
class UserGroup(SQLModel, table=True):
    """M2M User-Group intermediate table."""

    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    group_id: UUID = Field(foreign_key="group.id", primary_key=True)


class GroupOperationalUnit(SQLModel, table=True):
    """M2M Group-OperationalUnit intermediate table."""

    group_id: UUID = Field(foreign_key="group.id", primary_key=True)
    operational_unit_id: UUID = Field(
        foreign_key="operationalunit.id", primary_key=True
    )


class ScopesEnum(StrEnum):
    """API scopes enum."""

    # All (statique + dynamique)
    ALL_CREATE = "all:create"
    ALL_READ = "all:read"
    ALL_UPDATE = "all:update"
    ALL_DELETE = "all:delete"

    # Statique
    STATIC_CREATE = "static:create"
    STATIC_READ = "static:read"
    STATIC_UPDATE = "static:update"
    STATIC_DELETE = "static:delete"

    # Dynamique
    DYNAMIC_CREATE = "dynamic:create"
    DYNAMIC_READ = "dynamic:read"
    DYNAMIC_UPDATE = "dynamic:update"
    DYNAMIC_DELETE = "dynamic:delete"

    # Management
    MANAGE_READ = "manage:read"

    # Tariff
    TARIFF_CREATE = "tariff:create"
    TARIFF_READ = "tariff:read"
    TARIFF_UPDATE = "tariff:update"
    TARIFF_DELETE = "tariff:delete"


class PasswordCheckStatus(StrEnum):
    """Password check status."""

    VALID = "valid"
    INVALID = "invalid"
    OLD = "old"
    EXPIRED = "expired"


# -- Core schemas
class User(BaseAuditableSQLModel, table=True):
    """QualiCharge User."""

    __versioned__ = {
        "exclude": BaseAuditableSQLModel.__versioned__["exclude"]
        + ["password", "old_password"]
    }

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(unique=True, max_length=150)
    email: EmailStr = Field(unique=True, sa_type=String)
    first_name: Optional[str] = Field(max_length=150)
    last_name: Optional[str] = Field(max_length=150)
    password: str = Field(max_length=128)
    old_password: Optional[str] = Field(max_length=128)
    old_password_expires_at: Optional[FutureDatetime] = Field(
        sa_type=DateTime(timezone=True),
        description=("The timestamp indicating when the user's old password expires."),
        nullable=True,
    )  # type: ignore
    is_active: bool = False
    is_staff: bool = False
    is_superuser: bool = False
    last_login: PastDatetime = Field(
        sa_type=DateTime(timezone=True),
        description=(
            "The timestamp indicating when the user logged in for the last time."
        ),
        nullable=True,
    )  # type: ignore

    # Permissions
    scopes: List[ScopesEnum] = Field(sa_type=ARRAY(String), default=[])  # type: ignore[call-overload]

    # Relationships
    groups: list["Group"] = Relationship(back_populates="users", link_model=UserGroup)

    def model_dump(self, *args, **kwargs):
        """Serialize m2m."""
        dump = super().model_dump(*args, **kwargs)
        if "include" in kwargs and "groups" not in kwargs["include"]:
            return dump
        if "exclude" in kwargs and "groups" in kwargs["exclude"]:
            return dump
        dump["groups"] = [group.name for group in self.groups]
        return dump

    @property
    def operational_units(self):
        """Get user's linked operational units."""
        return [
            operational_unit
            for group in self.groups
            for operational_unit in group.operational_units
        ]

    def check_password(self, password: str) -> PasswordCheckStatus:
        """Check raw password hash compared to database hashed passwords.

        Returns:
            The password check status:
            - `valid`: the password validated against `password`
            - `old`: the password validated against `old_password` (grace period)
            - `expired`: the old password expired and cannot be used anymore
            - `invalid`: the password matches neither `password` nor `old_password`
        """
        if settings.PASSWORD_CONTEXT.verify(password, self.password):
            return PasswordCheckStatus.VALID

        # Should we fallback to the old password?
        if not self.old_password:
            return PasswordCheckStatus.INVALID

        # Does it expired?
        now = datetime.now(timezone.utc)
        if self.old_password_expires_at is None or self.old_password_expires_at < now:
            return PasswordCheckStatus.EXPIRED

        # Fallback to the old password with a warning
        if settings.PASSWORD_CONTEXT.verify(password, self.old_password):
            logger.warning("Old password is still in use for user %s", self.username)
            return PasswordCheckStatus.OLD
        return PasswordCheckStatus.INVALID

    def clean_old_password(self):
        """Clean old password.

        Should be called when the new password has been successfully used or when the
        old password expired.
        """
        self.old_password = None
        self.old_password_expires_at = None


class Group(BaseAuditableSQLModel, table=True):
    """QualiCharge Group."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, max_length=150)

    # Relationships
    users: list["User"] = Relationship(back_populates="groups", link_model=UserGroup)
    operational_units: list["OperationalUnit"] = Relationship(
        back_populates="groups", link_model=GroupOperationalUnit
    )
