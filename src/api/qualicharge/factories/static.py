"""QualiCharge static factories."""

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Generic, TypeVar
from uuid import uuid4

from faker import Faker
from geoalchemy2.types import Geometry
from polyfactory import Use
from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from pydantic_extra_types.coordinate import Coordinate

from ..models.static import Statique
from ..schemas.static import (
    Amenageur,
    Enseigne,
    Localisation,
    Operateur,
    PointDeCharge,
    Station,
)

T = TypeVar("T")


class FrenchDataclassFactory(Generic[T], DataclassFactory[T]):
    """Dataclass factory using the french locale."""

    __faker__ = Faker(locale="fr_FR")
    __is_base_factory__ = True


class StatiqueFactory(ModelFactory[Statique]):
    """Statique model factory."""

    contact_amenageur = Use(FrenchDataclassFactory.__faker__.ascii_company_email)
    contact_operateur = Use(FrenchDataclassFactory.__faker__.ascii_company_email)
    # FIXME
    #
    # Faker phone number factory randomly generates invalid data (as evaluated by the
    # phonenumbers library). We choose to use a less valuable factory to avoid flaky
    # tests.
    #
    # telephone_operateur = Use(FrenchDataclassFactory.__faker__.phone_number)
    telephone_operateur = Use(
        DataclassFactory.__random__.choice,
        [
            "+33144276350",
            "+33.1 44 27 63 50",
            "+33 (0)1 44 27 63 50",
            "+33 1 44 27 63 50",
            "0144276350",
            "01 44 27 63 50",
            "01-44-27-63-50",
            "(01)44276350",
        ],
    )
    puissance_nominale = Use(
        DataclassFactory.__faker__.pyfloat,
        right_digits=2,
        min_value=2.0,
        max_value=100.0,
    )
    date_maj = Use(DataclassFactory.__faker__.past_date)
    date_mise_en_service = Use(DataclassFactory.__faker__.past_date)
    id_station_itinerance = Use(
        FrenchDataclassFactory.__faker__.pystr_format, "FR###P######"
    )
    id_pdc_itinerance = Use(
        FrenchDataclassFactory.__faker__.pystr_format, "FR###E######"
    )


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


class AmenageurFactory(TimestampedSQLModelFactory[Amenageur]):
    """Amenageur schema factory."""

    contact_amenageur = Use(FrenchDataclassFactory.__faker__.ascii_company_email)


class EnseigneFactory(TimestampedSQLModelFactory[Enseigne]):
    """Enseigne schema factory."""


class CoordinateFactory(DataclassFactory[Coordinate]):
    """Coordinate factory."""

    longitude = Use(DataclassFactory.__faker__.pyfloat, min_value=-180, max_value=180)
    latitude = Use(DataclassFactory.__faker__.pyfloat, min_value=-90, max_value=90)


class LocalisationFactory(TimestampedSQLModelFactory[Localisation]):
    """Localisation schema factory."""

    @classmethod
    def get_sqlalchemy_types(cls) -> Dict[Any, Callable[[], Any]]:
        """Add support for Geometry fields."""
        types = super().get_sqlalchemy_types()
        return {
            Geometry: lambda: CoordinateFactory.build(),
            **types,
        }


class OperateurFactory(TimestampedSQLModelFactory[Operateur]):
    """Operateur schema factory."""

    contact_operateur = Use(FrenchDataclassFactory.__faker__.ascii_company_email)
    telephone_operateur = Use(FrenchDataclassFactory.__faker__.phone_number)


class PointDeChargeFactory(TimestampedSQLModelFactory[PointDeCharge]):
    """PointDeCharge schema factory."""

    id_pdc_itinerance = Use(
        FrenchDataclassFactory.__faker__.pystr_format, "FR###E######"
    )
    puissance_nominale = Use(
        DataclassFactory.__faker__.pyfloat,
        right_digits=2,
        min_value=2.0,
        max_value=100.0,
    )


class StationFactory(TimestampedSQLModelFactory[Station]):
    """Station schema factory."""

    id_station_itinerance = Use(
        FrenchDataclassFactory.__faker__.pystr_format, "FR###P######"
    )
    date_maj = Use(DataclassFactory.__faker__.past_date)
    date_mise_en_service = Use(DataclassFactory.__faker__.past_date)

    amenageur_id = None
    operateur_id = None
    enseigne_id = None
    localisation_id = None
