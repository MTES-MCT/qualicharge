"""QualiCharge dynamic factories."""

from datetime import timezone

from polyfactory import Use
from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.factories.pydantic_factory import ModelFactory

from ..conf import settings
from ..fixtures.operational_units import prefixes
from ..models.dynamic import SessionCreate, StatusCreate
from ..schemas.core import LatestStatus, Session, Status
from . import FrenchDataclassFactory, TimestampedSQLModelFactory


class SessionCreateFactory(ModelFactory[SessionCreate]):
    """Session model factory."""

    id_pdc_itinerance = Use(
        lambda: DataclassFactory.__random__.choice(prefixes)
        + FrenchDataclassFactory.__faker__.pystr_format("E######")
    )
    start = Use(
        lambda: DataclassFactory.__faker__.date_time_between(
            start_date=f"-{settings.API_MAX_SESSION_AGE}s",
            end_date=f"-{settings.API_MAX_SESSION_AGE - 3600}s",
            tzinfo=timezone.utc,
        )
    )
    end = Use(
        lambda: DataclassFactory.__faker__.date_time_between(
            start_date=f"-{settings.API_MAX_SESSION_AGE - 3600}s",
            tzinfo=timezone.utc,
        )
    )


class StatusCreateFactory(ModelFactory[StatusCreate]):
    """Status model factory."""

    id_pdc_itinerance = Use(
        lambda: DataclassFactory.__random__.choice(prefixes)
        + FrenchDataclassFactory.__faker__.pystr_format("E######")
    )
    horodatage = Use(
        lambda: DataclassFactory.__faker__.date_time_between(
            start_date=f"-{settings.API_MAX_STATUS_AGE}s", tzinfo=timezone.utc
        )
    )


class SessionFactory(TimestampedSQLModelFactory[Session]):
    """Session schema factory."""


class StatusFactory(TimestampedSQLModelFactory[Status]):
    """Status schema factory."""


class LatestStatusFactory(TimestampedSQLModelFactory[LatestStatus]):
    """LatestStatus schema factory."""
