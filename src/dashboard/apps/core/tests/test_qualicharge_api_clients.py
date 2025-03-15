"""Dashboard core qualicharge api clients tests."""

import pytest
from mock import AsyncMock, patch

from apps.core.qualicharge_api.adapters import ManageStationsAdapter
from apps.core.qualicharge_api.clients import (
    ManageStationClient,
    QualiChargeApi,
    QualiChargeBaseClient,
)

API_RESPONSE_COMPANY_INFO = [
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
    {
        "id_station_itinerance": "FR073P03STATIONC",
        "nom_station": "Station C",
        "num_pdl": "30002100000000",
        "updated_at": "2025-03-12T15:49:43.477800Z",
    },
]


def test_qualicharge_base_client_initialization(settings):
    """Test the initialization of QualiChargeBaseClient."""
    # initialize API settings
    settings.QCC_API_LOGIN_USERNAME = "admin"
    settings.QCC_API_LOGIN_PASSWORD = "admin"  # noqa: S105
    settings.QCC_API_ROOT_URL = "http://api:8000/api/v1"

    with patch("apps.core.qualicharge_api.clients.QCC") as mock_qcc_client:
        # initialize API
        api_client = QualiChargeBaseClient()

        # Assert that settings are loaded correctly
        assert api_client.username == "admin"
        assert api_client.password == "admin"  # noqa: S105
        assert api_client.api_root_url == "http://api:8000/api/v1"

        # Ensure the QCC client is initialized with the correct parameters
        mock_qcc_client.assert_called_once_with(
            api_client.username, api_client.password, api_client.api_root_url
        )


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_manage_stations_list_is_valid(monkeypatch):
    """Tests if the ManageStationClient.list method returns the expected data."""

    # Mock qcc read_stations response
    async def mock_read_stations(*args):
        for station in API_RESPONSE_COMPANY_INFO:
            yield station

    # Mock client.manage.read_stations()
    mock_client = AsyncMock()
    mock_client.manage.read_stations = mock_read_stations

    # Patch QualiChargeBaseClient._get
    monkeypatch.setattr(
        "apps.core.qualicharge_api.clients.QCC",
        lambda self, s, a: mock_client,
    )

    # Test ManageStationClient.list
    client = ManageStationClient()
    siren = "123456789"
    result = await client.list(siren)

    assert len(result) == len(API_RESPONSE_COMPANY_INFO)
    for result_data, expected in zip(result, API_RESPONSE_COMPANY_INFO, strict=True):
        assert isinstance(result_data, ManageStationsAdapter)
        assert result_data.id_station_itinerance == expected["id_station_itinerance"]
        assert result_data.nom_station == expected["nom_station"]
        assert result_data.num_pdl == expected["num_pdl"]
        assert result_data.updated_at == expected["updated_at"]


@pytest.mark.django_db
def test_qualicharge_api_facade_with_valid_data(monkeypatch):
    """Tests QualiChargeApi.manage_stations_list method with valid data."""
    siren = "123456789"
    mock_response = [
        ManageStationsAdapter(
            id_station_itinerance="FR073P01STATIONA",
            nom_station="Station A",
            num_pdl="50088800000000",
            updated_at="2025-03-12T15:49:43.477800Z",
        ),
        ManageStationsAdapter(
            id_station_itinerance="FR073P02STB",
            nom_station="Station B",
            num_pdl="50088800000000",
            updated_at="2025-03-12T15:49:43.477800Z",
        ),
    ]

    # mock ManageStationClient.list() response
    async def mock_manage_stations_list(*args):
        return mock_response

    # Patch ManageStationClient.list()
    monkeypatch.setattr(
        "apps.core.qualicharge_api.clients.ManageStationClient.list",
        AsyncMock(side_effect=mock_manage_stations_list),
    )

    # Test api.manage_stations_list()
    api = QualiChargeApi()
    result = api.manage_stations_list(siren)

    ManageStationClient.list.assert_called_once_with(siren, None)
    assert result == mock_response
    for result_data, expected in zip(result, mock_response, strict=True):
        assert isinstance(result_data, ManageStationsAdapter)
        assert result_data.id_station_itinerance == expected.id_station_itinerance
        assert result_data.nom_station == expected.nom_station
        assert result_data.num_pdl == expected.num_pdl
        assert result_data.updated_at == expected.updated_at
