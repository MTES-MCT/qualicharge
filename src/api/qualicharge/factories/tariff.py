"""QualiCharge tariff factories."""

from datetime import datetime, timedelta, timezone
from typing import Any

from polyfactory import Use
from polyfactory.decorators import post_generated
from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from ..models.tariff import (
    PointDeChargeTariffCreate,
    PriceComponentTypeEnum,
    TariffCreate,
    TariffElement,
    TariffObject,
)
from ..schemas.tariff import PointDeChargeTariff, Tariff
from . import AuditableSQLModelFactory, SoftDeleteFactoryMixin


class TariffElementFactory(ModelFactory[TariffElement]):
    """Tariff element model factory."""

    price_components = Use(
        lambda: [
            {
                "type": PriceComponentTypeEnum.ENERGY,
                "price": DataclassFactory.__faker__.pyfloat(
                    right_digits=2,
                    min_value=0.01,
                    max_value=1.0,
                ),
                "step_size": 1,
            }
        ]
    )
    restrictions = None


class TariffObjectFactory(ModelFactory[TariffObject]):
    """Tariff object model factory."""

    country_code = "FR"
    party_id = "QCH"
    id = Use(DataclassFactory.__faker__.uuid4)
    currency = "EUR"
    elements = Use(lambda: [TariffElementFactory.build()])
    tariff_alt_text = Use(lambda: [{"language": "fr", "text": "Tarif simple"}])
    start_date_time = Use(
        lambda: datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=1)
    )
    last_updated = Use(
        lambda: datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=1)
    )
    tax_included = "YES"
    min_price = None
    max_price = None

    @post_generated
    @classmethod
    def end_date_time(cls, start_date_time: datetime):
        """Ensure application dates are consistent."""
        return start_date_time + timedelta(days=2)

    @classmethod
    def build(
        cls,
        factory_use_construct: bool = False,
        **kwargs: Any,
    ) -> TariffObject:
        """Build a tariff object accepting the model field name as a convenience."""
        if "tariff_id" in kwargs:
            kwargs["id"] = kwargs.pop("tariff_id")
        return super().build(factory_use_construct=factory_use_construct, **kwargs)


class TariffCreateFactory(ModelFactory[TariffCreate]):
    """Tariff creation payload factory."""

    tariff = Use(TariffObjectFactory.build)
    targets: list[str] = []

    @classmethod
    def build(
        cls,
        factory_use_construct: bool = False,
        **kwargs: Any,
    ) -> TariffCreate:
        """Build a payload accepting the model field name as a convenience."""
        if "id_pdc_itinerance" in kwargs:
            kwargs["targets"] = kwargs.pop("id_pdc_itinerance")
        return super().build(factory_use_construct=factory_use_construct, **kwargs)


class PointDeChargeTariffCreateFactory(ModelFactory[PointDeChargeTariffCreate]):
    """Point de charge tariff association payload factory."""

    original_id = Use(DataclassFactory.__faker__.uuid4)
    original_last_updated = Use(
        lambda: datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=1)
    )
    id_pdc_itinerance = Use(lambda: ["FRS63E0001"])


class TariffFactory(SoftDeleteFactoryMixin, AuditableSQLModelFactory[Tariff]):
    """Tariff schema factory."""

    original_id = Use(DataclassFactory.__faker__.uuid4)
    original_last_updated = Use(
        lambda: datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=1)
    )
    start = Use(
        lambda: datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=1)
    )
    end = Use(
        lambda: datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=1)
    )

    @post_generated
    @classmethod
    def raw(
        cls,
        original_id: str,
        original_last_updated: datetime,
        start: datetime,
        end: datetime,
    ):
        """Keep indexed fields and the raw tariff object aligned."""
        return TariffObjectFactory.build(
            tariff_id=original_id,
            last_updated=original_last_updated,
            start_date_time=start,
            end_date_time=end,
        ).model_dump(by_alias=True, mode="json")


class PointDeChargeTariffFactory(
    SQLAlchemyFactory[PointDeChargeTariff],
):
    """Point de charge tariff association schema factory."""

    __set_relationships__ = False

    created_at = Use(lambda: datetime.now(timezone.utc) - timedelta(hours=1))
    updated_at = Use(datetime.now, timezone.utc)
    created_by_id = None
    updated_by_id = None
