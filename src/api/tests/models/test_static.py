"""QualiCharge static models tests."""

from pydantic_extra_types.coordinate import Coordinate

from qualicharge.factories.static import StatiqueFactory
from qualicharge.models.static import Statique


def test_statique_model_coordonneesXY():
    """Test the Statique model coordonneesXY field."""
    telephone_operateur = "0123456789"
    id_station_itinerance = "ESZUNP8891687432127666088"
    id_pdc_itinerance = "ESZUNE1111ER1"
    longitude = 12.3
    latitude = 16.2

    # Expected raw input
    record = StatiqueFactory.build(
        telephone_operateur=telephone_operateur,
        id_station_itinerance=id_station_itinerance,
        id_pdc_itinerance=id_pdc_itinerance,
        coordonneesXY=f"[{longitude},{latitude}]",
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude

    # Tuple input
    record = StatiqueFactory.build(
        telephone_operateur=telephone_operateur,
        id_station_itinerance=id_station_itinerance,
        id_pdc_itinerance=id_pdc_itinerance,
        coordonneesXY=(latitude, longitude),
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude

    # Coordinate input
    record = StatiqueFactory.build(
        telephone_operateur=telephone_operateur,
        id_station_itinerance=id_station_itinerance,
        id_pdc_itinerance=id_pdc_itinerance,
        coordonneesXY=Coordinate(latitude, longitude),
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude


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
