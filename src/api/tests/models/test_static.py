"""QualiCharge static models tests."""

import pytest
from pydantic_extra_types.coordinate import Coordinate

from qualicharge.factories.static import StatiqueFactory
from qualicharge.models.static import Statique


def test_statique_model_coordonneesXY():
    """Test the Statique model coordonneesXY field."""
    longitude = 12.3
    latitude = 16.2

    # Expected raw input
    record = StatiqueFactory.build(
        coordonneesXY=f"[{longitude},{latitude}]",
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude

    # Tuple input
    record = StatiqueFactory.build(
        coordonneesXY=(latitude, longitude),
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude

    # Coordinate input
    record = StatiqueFactory.build(
        coordonneesXY=Coordinate(latitude, longitude),
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude


@pytest.mark.parametrize(
    "phone_number",
    (
        "+33144276350",
        "+33.1 44 27 63 50",
        "+33 (0)1 44 27 63 50",
        "+33 (0) 1 44 27 63 50",
        "+33 1 44 27 63 50",
        "0144276350",
        "01 44 27 63 50",
        "01-44-27-63-50",
        "(01)44276350",
    ),
)
def test_statique_model_french_phone_numbers(phone_number):
    """Test all french phone numbers formats."""
    statique = StatiqueFactory.build(telephone_operateur=phone_number)
    assert statique.telephone_operateur == "tel:+33-1-44-27-63-50"


def test_statique_model_json_schema():
    """Test the Statique model generated JSON schema."""
    schema = Statique.model_json_schema()

    expected_description = (
        "coordonneesXY is supposed to be a '[longitude,latitude]' array string"
    )
    assert schema["properties"]["coordonneesXY"]["type"] == "string"
    assert schema["properties"]["coordonneesXY"]["title"] == "coordonneesXY"
    assert schema["properties"]["coordonneesXY"]["description"] == expected_description
    assert schema["properties"]["coordonneesXY"]["examples"] == ["[12.3, 41.5]"]


def test_statique_model_afirev_previx_check():
    """Test the id_pdc/station_itinerance consistency."""
    with pytest.raises(
        ValueError,
        match=(
            "AFIREV prefixes from id_station_itinerance and "
            "id_pdc_itinerance do not match"
        ),
    ):
        StatiqueFactory.build(
            id_pdc_itinerance="FR147E0042", id_station_itinerance="FR073P00001"
        )

    # Should be a valid usage
    StatiqueFactory.build(
        id_pdc_itinerance="FR073E0042", id_station_itinerance="FR073P00001"
    )

    # Default factory behavior should be consistent
    StatiqueFactory.build()
