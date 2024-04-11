"""QualiCharge dynamic factories."""

from polyfactory.factories.pydantic_factory import ModelFactory

from ..models.dynamic import Status


class StatusFactory(ModelFactory[Status]):
    """Status model factory."""
