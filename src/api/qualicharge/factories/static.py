"""QualiCharge static factories."""

from typing import Any, Callable, Dict, TypeVar

from geoalchemy2.types import Geometry
from polyfactory import Use
from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic_extra_types.coordinate import Coordinate

from ..fixtures.operational_units import prefixes
from ..models.static import Statique
from ..schemas import (
    Amenageur,
    Enseigne,
    Localisation,
    Operateur,
    OperationalUnit,
    PointDeCharge,
    Station,
)
from . import FrenchDataclassFactory, TimestampedSQLModelFactory

T = TypeVar("T")


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
        lambda: DataclassFactory.__random__.choice(prefixes)
        + FrenchDataclassFactory.__faker__.pystr_format("P######")
    )
    id_pdc_itinerance = Use(
        lambda: DataclassFactory.__random__.choice(prefixes)
        + FrenchDataclassFactory.__faker__.pystr_format("E######")
    )


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
        lambda: DataclassFactory.__random__.choice(prefixes)
        + FrenchDataclassFactory.__faker__.pystr_format("E######")
    )
    puissance_nominale = Use(
        DataclassFactory.__faker__.pyfloat,
        right_digits=2,
        min_value=2.0,
        max_value=100.0,
    )


class OperationalUnitFactory(TimestampedSQLModelFactory[OperationalUnit]):
    """OperationalUnit schema factory."""

    code = Use(DataclassFactory.__random__.choice, prefixes)
    name = Use(FrenchDataclassFactory.__faker__.company)


class StationFactory(TimestampedSQLModelFactory[Station]):
    """Station schema factory."""

    id_station_itinerance = Use(
        lambda: DataclassFactory.__random__.choice(prefixes)
        + FrenchDataclassFactory.__faker__.pystr_format("P######")
    )
    date_maj = Use(DataclassFactory.__faker__.past_date)
    date_mise_en_service = Use(DataclassFactory.__faker__.past_date)

    amenageur_id = None
    operateur_id = None
    enseigne_id = None
    localisation_id = None
    operational_unit_id = None
