"""QualiCharge authentication schemas."""

from enum import StrEnum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy.types import ARRAY, String
from sqlmodel import Field, Relationship, SQLModel

from qualicharge.schemas import BaseTimestampedSQLModel

if TYPE_CHECKING:
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
    is_active: bool = False
    is_staff: bool = False
    is_superuser: bool = False

    # Permissions
    scopes: List[ScopesEnum] = Field(sa_type=ARRAY(String))

    # Relationships
    groups: list["Group"] = Relationship(back_populates="users", link_model=UserGroup)


class Group(BaseTimestampedSQLModel, table=True):
    """QualiCharge Group."""

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(unique=True, max_length=150)

    # Relationships
    users: list["User"] = Relationship(back_populates="groups", link_model=UserGroup)
    operational_units: list["OperationalUnit"] = Relationship(
        back_populates="groups", link_model=GroupOperationalUnit
    )