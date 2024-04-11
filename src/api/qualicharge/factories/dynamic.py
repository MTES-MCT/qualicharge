"""QualiCharge dynamic factories."""

from polyfactory.factories.pydantic_factory import ModelFactory

from ..models.dynamic import Session, Status


class SessionFactory(ModelFactory[Session]):
    """Session model factory."""


class StatusFactory(ModelFactory[Status]):
    """Status model factory."""
