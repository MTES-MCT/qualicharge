"""QualiCharge dynamic factories."""

from polyfactory.factories.pydantic_factory import ModelFactory

from ..models.dynamic import SessionCreate, StatusCreate


class SessionCreateFactory(ModelFactory[SessionCreate]):
    """Session model factory."""


class StatusCreateFactory(ModelFactory[StatusCreate]):
    """Status model factory."""
