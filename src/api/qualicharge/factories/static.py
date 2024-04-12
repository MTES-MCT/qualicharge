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


class StatiqueFactory(ModelFactory[Statique]):
    """Statique model factory."""


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

    puissance_nominale = Use(
        DataclassFactory.__faker__.pyfloat,
        right_digits=2,
        min_value=2.0,
        max_value=100.0,
    )


class StationFactory(TimestampedSQLModelFactory[Station]):
    """Station schema factory."""

    date_maj = Use(DataclassFactory.__faker__.past_date)
    date_mise_en_service = Use(DataclassFactory.__faker__.past_date)

    amenageur_id = None
    operateur_id = None
    enseigne_id = None
    localisation_id = None
