"""Dashboard core qualicharge api adapters tests."""

import pytest

from apps.core.qualicharge_api.adapters import ManageStationsAdapter


@pytest.mark.parametrize(
    "data",
    [
        {
            "id_station_itinerance": "FR073P01STATIONA",
            "nom_station": "Station A",
            "num_pdl": "50088800000000",
            "updated_at": "2025-03-12T15:49:43.477800Z",
        },
        {
            "id_station_itinerance": "FR073P02STB",
            "nom_station": "Station B",
            "num_pdl": "30000110910030",
            "updated_at": "2025-03-12T15:49:43.477800Z",
        },
    ],
)
def test_manage_stations_adapter_initialization(data):
    """Tests initialization of the ManageStationsAdapter."""
    station = ManageStationsAdapter.from_api_response(data)
    assert station.id_station_itinerance == data["id_station_itinerance"]
    assert station.nom_station == data["nom_station"]
    assert station.num_pdl == data["num_pdl"]
    assert station.updated_at == data["updated_at"]


def test_manage_stations_adapter_missing_attributs():
    """Tests handling of missing key."""
    data = {}
    station = ManageStationsAdapter.from_api_response(data)
    assert station.id_station_itinerance == ""
    assert station.nom_station == ""
    assert station.num_pdl == ""
    assert station.updated_at == ""
