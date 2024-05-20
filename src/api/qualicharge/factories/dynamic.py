"""QualiCharge dynamic factories."""

from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory

from ..models.dynamic import SessionCreate, StatusCreate
from ..schemas.core import Status
from . import FrenchDataclassFactory, TimestampedSQLModelFactory


class SessionCreateFactory(ModelFactory[SessionCreate]):
    """Session model factory."""

    id_pdc_itinerance = Use(
        FrenchDataclassFactory.__faker__.pystr_format, "FR###E######"
    )


class StatusCreateFactory(ModelFactory[StatusCreate]):
    """Status model factory."""

    id_pdc_itinerance = Use(
        FrenchDataclassFactory.__faker__.pystr_format, "FR###E######"
    )


class StatusFactory(TimestampedSQLModelFactory[Status]):
    """Status schema factory."""
