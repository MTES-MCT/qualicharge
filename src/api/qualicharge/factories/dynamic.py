"""QualiCharge dynamic factories."""

from polyfactory import Use
from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.factories.pydantic_factory import ModelFactory

from ..fixtures.operational_units import prefixes
from ..models.dynamic import SessionCreate, StatusCreate
from ..schemas.core import Session, Status
from . import FrenchDataclassFactory, TimestampedSQLModelFactory


class SessionCreateFactory(ModelFactory[SessionCreate]):
    """Session model factory."""

    id_pdc_itinerance = Use(
        lambda: DataclassFactory.__random__.choice(prefixes)
        + FrenchDataclassFactory.__faker__.pystr_format("E######")
    )


class StatusCreateFactory(ModelFactory[StatusCreate]):
    """Status model factory."""

    id_pdc_itinerance = Use(
        lambda: DataclassFactory.__random__.choice(prefixes)
        + FrenchDataclassFactory.__faker__.pystr_format("E######")
    )


class SessionFactory(TimestampedSQLModelFactory[Session]):
    """Session schema factory."""


class StatusFactory(TimestampedSQLModelFactory[Status]):
    """Status schema factory."""
