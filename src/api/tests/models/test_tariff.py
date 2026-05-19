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
    assert tariff.tariff_id == f"{tariff.country_code}{tariff.party_id}{tariff.id}"
    assert tariff.currency == "EUR"
    assert tariff.elements
    assert tariff.start_date_time < tariff.end_date_time
    assert tariff.last_updated.tzinfo is not None
    assert tariff.model_dump(by_alias=True, mode="json")["id"] == tariff.id


def test_tariff_create_factory():
    """Test the tariff create payload factory."""
    payload = TariffCreateFactory.build()

    assert payload.tariff.tariff_id
    assert payload.targets == []


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
        country_code="FR",
        party_id="QCH",
        id="tariff-1",
        last_updated=now,
        elements=[{"price_components": [{"type": "ENERGY", "price": 0.3}]}],
    )

    assert tariff.id == "tariff-1"
    assert tariff.tariff_id == "FRQCHtariff-1"
    assert tariff.model_dump(by_alias=True, mode="json")["id"] == "tariff-1"


@pytest.mark.parametrize("field", ["country_code", "party_id"])
def test_tariff_object_requires_ocpi_identifiers(field):
    """Test tariff object requires OCPI ownership identifiers."""
    payload = {
        "country_code": "FR",
        "party_id": "QCH",
        "id": "tariff-1",
        "last_updated": datetime.now(timezone.utc),
        "elements": [{"price_components": [{"type": "ENERGY", "price": 0.3}]}],
    }
    payload.pop(field)

    with pytest.raises(ValidationError, match="Field required"):
        TariffObject(**payload)


def test_tariff_object_tariff_alt_url():
    """Test tariff object alternative URL validation and serialization."""
    tariff_alt_url = "https://example.com/tariffs/tariff-1"
    tariff = TariffObjectFactory.build(tariff_alt_url=tariff_alt_url)

    assert str(tariff.tariff_alt_url) == tariff_alt_url
    assert tariff.model_dump(by_alias=True, mode="json")["tariff_alt_url"] == (
        tariff_alt_url
    )


def test_tariff_object_tariff_alt_url_max_length():
    """Test tariff object alternative URL should not exceed 255 characters."""
    tariff_alt_url = f"https://example.com/{'a' * 236}"

    with pytest.raises(ValidationError, match="at most 255"):
        TariffObjectFactory.build(tariff_alt_url=tariff_alt_url)


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


def test_tariff_object_cannot_end_before_last_updated():
    """Test tariff object end date cannot be before its last update."""
    now = datetime.now(timezone.utc)

    with pytest.raises(
        ValueError,
        match="Tariff FRQCHtariff-1 cannot end before his last updated time.",
    ):
        TariffObjectFactory.build(
            id="tariff-1",
            last_updated=now,
            end_date_time=now - timedelta(seconds=1),
        )


def test_tariff_object_can_have_no_end_date_after_last_updated():
    """Test tariff object without end date is valid after its last update."""
    now = datetime.now(timezone.utc)

    tariff = TariffObjectFactory.build(
        last_updated=now,
        end_date_time=None,
    )

    assert tariff.end_date_time is None


def test_tariff_object_restricts_type_to_ad_hoc_payment():
    """Test tariff object type should be AD_HOC_PAYMENT when provided."""
    with pytest.raises(
        ValueError,
        match="Tariff FRQCHtariff-1 type must be 'AD_HOC_PAYMENT'.",
    ):
        TariffObjectFactory.build(id="tariff-1", type="REGULAR")


def test_tariff_object_restricts_currency_to_eur():
    """Test tariff object currency should be EUR when provided."""
    with pytest.raises(
        ValueError,
        match="Tariff FRQCHtariff-1 currency must be 'EUR'.",
    ):
        TariffObjectFactory.build(id="tariff-1", currency="USD")


def test_tariff_object_rejects_tax_included_na():
    """Test tariff object tax_included should not be N/A when provided."""
    with pytest.raises(
        ValueError,
        match="Tariff FRQCHtariff-1 tax_included must not be 'NA'.",
    ):
        TariffObjectFactory.build(id="tariff-1", tax_included="N/A")


def test_tariff_object_allows_optional_business_fields():
    """Test tariff object business fields can still be omitted."""
    tariff = TariffObjectFactory.build(type=None, currency=None, tax_included=None)

    assert tariff.type is None
    assert tariff.currency is None
    assert tariff.tax_included is None


def test_tariff_object_computed_properties():
    """Test tariff object useful computed properties."""
    last_updated = datetime(2026, 2, 23, 10, tzinfo=timezone.utc)
    start_date_time = last_updated - timedelta(hours=1)
    tariff = TariffObjectFactory.build(
        id="tariff-1",
        last_updated=last_updated,
        start_date_time=start_date_time,
        tax_included="YES",
    )

    assert tariff.tariff_application_date == last_updated
    assert tariff.tariff_id == "FRQCHtariff-1"
    assert tariff.ocpi_version == "2.3"
    assert tariff.is_tax_included is True
    assert "tariff_id" not in tariff.model_dump(mode="json")


def test_tariff_object_application_date_uses_later_start_date():
    """Test tariff object application date uses start date when later."""
    last_updated = datetime(2026, 2, 23, 10, tzinfo=timezone.utc)
    start_date_time = last_updated + timedelta(hours=1)
    tariff = TariffObjectFactory.build(
        last_updated=last_updated,
        start_date_time=start_date_time,
        end_date_time=start_date_time + timedelta(hours=1),
    )

    assert tariff.tariff_application_date == start_date_time


def test_tariff_object_computed_tax_properties_for_ocpi_22():
    """Test tax computed properties for tariffs without tax_included."""
    tariff = TariffObjectFactory.build(tax_included=None)

    assert tariff.ocpi_version == "2.2"
    assert tariff.is_tax_included is False


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


@pytest.mark.parametrize("vat", [None, 0.0, 20.0, 100.0])
def test_price_component_vat_is_valid_percentage(vat):
    """Test price component VAT can be omitted or set to a valid percentage."""
    component = PriceComponent(type="ENERGY", price=0.3, vat=vat)

    assert component.vat == vat


@pytest.mark.parametrize("vat", [-0.01, 100.01])
def test_price_component_vat_must_be_valid_percentage(vat):
    """Test price component VAT should be between 0 and 100."""
    with pytest.raises(ValidationError, match="VAT must be between 0 and 100."):
        PriceComponent(type="ENERGY", price=0.3, vat=vat)


def test_tariff_element_price_components_required():
    """Test tariff elements require at least one price component."""
    with pytest.raises(ValidationError, match="List should have at least 1 item"):
        TariffElement(price_components=[])


def test_point_de_charge_tariff_create_requires_pdc():
    """Test tariff association payload requires at least one point of charge."""
    with pytest.raises(ValidationError, match="List should have at least 1 item"):
        PointDeChargeTariffCreate(
            original_id="FRQCHtariff-1",
            original_last_updated=datetime.now(timezone.utc),
            id_pdc_itinerance=[],
        )
