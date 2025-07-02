"""QualiCharge factories."""

from datetime import datetime, timedelta, timezone
from typing import Generic, TypeVar
from uuid import uuid4

from faker import Faker
from polyfactory import Use
from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

T = TypeVar("T")


class FrenchDataclassFactory(Generic[T], DataclassFactory[T]):
    """Dataclass factory using the french locale."""

    __faker__ = Faker(locale="fr_FR")
    __is_base_factory__ = True


class TimestampedSQLModelFactory(Generic[T], SQLAlchemyFactory[T]):
    """A base factory for timestamped SQLModel.

    We expect SQLModel to define the following fields:

    - id: UUID
    - created_at: datetime
    - updated_at: datetime
    """

    __is_base_factory__ = True

    id = Use(uuid4)
    created_at = Use(lambda: datetime.now(timezone.utc) - timedelta(hours=1))
    updated_at = Use(datetime.now, timezone.utc)


class AuditableSQLModelFactory(Generic[T], SQLAlchemyFactory[T]):
    """A base factory for Auditable SQLModel.

    We expect SQLModel to define the following fields:

    - id: UUID
    - created_at: datetime
    - updated_at: datetime
    - created_by_id: UUID
    - updated_by_id: UUID
    """

    __is_base_factory__ = True

    id = Use(uuid4)
    created_at = Use(lambda: datetime.now(timezone.utc) - timedelta(hours=1))
    updated_at = Use(datetime.now, timezone.utc)
    created_by_id = None
    updated_by_id = None


class SoftDeleteFactoryMixin:
    """A mixin for SoftDelete models."""

    deleted_by_id = None
    deleted_at = None
