"""QualiCharge authentication schemas."""

from enum import StrEnum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import EmailStr, PastDatetime
from sqlalchemy.types import ARRAY, DateTime, String
from sqlmodel import Field, Relationship, SQLModel

from qualicharge.conf import settings
from qualicharge.schemas import BaseTimestampedSQLModel
from qualicharge.schemas.core import OperationalUnit


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


# -- Core schemas
class User(BaseTimestampedSQLModel, table=True):
    """QualiCharge User."""

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    username: str = Field(unique=True, max_length=150)
    email: EmailStr = Field(unique=True, sa_type=String)
    first_name: Optional[str] = Field(max_length=150)
    last_name: Optional[str] = Field(max_length=150)
    password: str = Field(max_length=128)
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

    def check_password(self, password: str) -> bool:
        """Check raw password hash compared to database hashed password."""
        return settings.PASSWORD_CONTEXT.verify(password, self.password)


class Group(BaseTimestampedSQLModel, table=True):
    """QualiCharge Group."""

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(unique=True, max_length=150)

    # Relationships
    users: list["User"] = Relationship(back_populates="groups", link_model=UserGroup)
    operational_units: list["OperationalUnit"] = Relationship(
        back_populates="groups", link_model=GroupOperationalUnit
    )
