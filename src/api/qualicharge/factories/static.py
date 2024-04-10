"""QualiCharge static factories."""

from polyfactory.factories.pydantic_factory import ModelFactory

from ..models.static import Statique


class StatiqueFactory(ModelFactory[Statique]):
    """Statique model factory."""
