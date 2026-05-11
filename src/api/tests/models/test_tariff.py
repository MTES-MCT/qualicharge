"""QualiCharge tariff models tests."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from qualicharge.factories.tariff import (
    PointDeChargeTariffCreateFactory,
    TariffCreateFactory,
    TariffObjectFactory,
)
from qualicharge.models.tariff import (
    PointDeChargeTariffCreate,
    PriceComponent,
    TariffElement,
    TariffObject,
)


def test_tariff_object_factory():
    """Test the tariff object model factory."""
    tariff = TariffObjectFactory.build()

    assert tariff.tariff_id
    assert tariff.currency == "EUR"
    assert tariff.elements
    assert tariff.start_date_time < tariff.end_date_time
    assert tariff.last_updated.tzinfo is not None
    assert tariff.model_dump(by_alias=True, mode="json")["id"] == tariff.tariff_id


def test_tariff_create_factory():
    """Test the tariff create payload factory."""
    payload = TariffCreateFactory.build()

    assert payload.tariff.tariff_id
    assert payload.id_pdc_itinerance == []


def test_point_de_charge_tariff_create_factory():
    """Test the tariff association payload factory."""
    payload = PointDeChargeTariffCreateFactory.build()

    assert payload.original_id
    assert payload.original_last_updated is not None
    assert payload.id_pdc_itinerance == ["FRS63E0001"]


def test_tariff_object_alias():
    """Test tariff object input and output aliases."""
    now = datetime.now(timezone.utc)
    tariff = TariffObject(
        id="tariff-1",
        last_updated=now,
        elements=[{"price_components": [{"type": "ENERGY", "price": 0.3}]}],
    )

    assert tariff.tariff_id == "tariff-1"
    assert tariff.model_dump(by_alias=True, mode="json")["id"] == "tariff-1"


def test_tariff_object_application_dates_consistency():
    """Test tariff object start/end application dates consistency."""
    now = datetime.now(timezone.utc)

    with pytest.raises(
        ValueError,
        match="A tariff cannot start after it has ended.",
    ):
        TariffObjectFactory.build(
            start_date_time=now,
            end_date_time=now - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "field",
    [
        "last_updated",
        "start_date_time",
        "end_date_time",
    ],
)
def test_tariff_object_datetime_fields_are_timezone_aware(field):
    """Test TariffObject datetime fields should be aware."""
    now = datetime.now()

    with pytest.raises(ValidationError, match="Input should have timezone info"):
        TariffObjectFactory.build(**{field: now})


@pytest.mark.parametrize(
    "value",
    [
        -0.01,
        -1.0,
    ],
)
def test_price_component_price_positive(value):
    """Test price components cannot have a negative price."""
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        PriceComponent(type="ENERGY", price=value)


def test_tariff_element_price_components_required():
    """Test tariff elements require at least one price component."""
    with pytest.raises(ValidationError, match="List should have at least 1 item"):
        TariffElement(price_components=[])


def test_point_de_charge_tariff_create_requires_pdc():
    """Test tariff association payload requires at least one point of charge."""
    with pytest.raises(ValidationError, match="List should have at least 1 item"):
        PointDeChargeTariffCreate(original_id="tariff-1", id_pdc_itinerance=[])

