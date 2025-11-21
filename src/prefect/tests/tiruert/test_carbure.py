"""QualiCharge prefect tiruert tests: Carbure."""

import pytest
import requests

from tiruert.carbure import CarbureClient


def test_carbure_client_init(carbure_config):
    """Test the CarbureClient initanciation."""
    client = CarbureClient(carbure_config)

    assert client.root_url == carbure_config.root_url
    assert client.user == carbure_config.user
    assert client.session.headers == {
        "Accept": "application/json",
        "X-Api-Key": carbure_config.user.api_key,
    }
    assert client.access_token is None
    assert client.refresh_token is None


def test_carbure_client_auth(responses, carbure_config):
    """Test the carbure API client authentication."""
    client = CarbureClient(carbure_config)

    # Initial state
    assert client.access_token is None
    assert client.refresh_token is None

    # Perform initial authentication
    responses.post(
        f"{carbure_config.root_url}api/token/",
        status=200,
        json={
            "access": "access",
            "refresh": "refresh",
        },
    )
    client._auth()
    assert client.access_token == "access"  # noqa: S105
    assert client.refresh_token == "refresh"  # noqa: S105

    # Refresh
    responses.post(
        f"{carbure_config.root_url}api/token/refresh/",
        status=200,
        json={
            "access": "refreshed access",
        },
    )
    client._auth()
    assert client.access_token == "refreshed access"  # noqa: S105
    assert client.refresh_token == "refresh"  # noqa: S105


def test_carbure_ensure_auth(responses, carbure_config):
    """Test the client enforces authentication when required."""
    client = CarbureClient(carbure_config)

    # Initial state: not authenticated
    assert client.access_token is None
    assert client.refresh_token is None

    # Mock expected scenario: not authenticated
    # 1. Perform initial request
    responses.get(
        f"{carbure_config.root_url}api/resources/entities",
        status=403,
    )
    # 2. Authenticate
    responses.post(
        f"{carbure_config.root_url}api/token/",
        status=200,
        json={
            "access": "access",
            "refresh": "refresh",
        },
    )
    # 3. Re-submit the initial request
    responses.get(
        f"{carbure_config.root_url}api/resources/entities",
        status=200,
        json=[{"name": "foo"}],
    )
    entities = client.check_entities()
    assert client.access_token == "access"  # noqa: S105
    assert client.refresh_token == "refresh"  # noqa: S105
    assert entities == [{"name": "foo"}]

    # Mock expected scenario: expired token
    # 1. Perform initial request
    responses.get(
        f"{carbure_config.root_url}api/resources/entities",
        status=401,
    )
    # 2. Authenticate
    responses.post(
        f"{carbure_config.root_url}api/token/refresh/",
        status=200,
        json={
            "access": "refreshed access",
        },
    )
    # 3. Re-submit the initial request
    responses.get(
        f"{carbure_config.root_url}api/resources/entities",
        status=200,
        json=[{"name": "foo"}],
    )
    entities = client.check_entities()
    assert client.access_token == "refreshed access"  # noqa: S105
    assert client.refresh_token == "refresh"  # noqa: S105
    assert entities == [{"name": "foo"}]


def test_carbure_check_entities(responses, carbure_client):
    """Test the client `check_entities` requests."""
    responses.get(
        f"{carbure_client.root_url}api/resources/entities",
        status=200,
        json=[{"name": "foo"}],
    )
    entities = carbure_client.check_entities()
    assert entities == [{"name": "foo"}]


def test_carbure_bulk_create_certificates(responses, carbure_client):
    """Test the client `bulk_create_certificates` requests."""
    certificates = [
        {
            "entity": "Foo Inc.",
            "siren": "123456789",
            "operational_units": [
                {
                    "code": "FRXXX",
                    "from": "2025-01-01",
                    "to": "2025-01-31",
                    "stations": [
                        {"id": "FRXXXP001", "energy": 123.4, "is_controlled": True},
                        {"id": "FRXXXP002", "energy": 567.8, "is_controlled": False},
                    ],
                },
                {
                    "code": "FRYYY",
                    "from": "2025-01-01",
                    "to": "2025-01-31",
                    "stations": [
                        {"id": "FRYYYP001", "energy": 123.4, "is_controlled": True},
                        {"id": "FRYYYP002", "energy": 567.8, "is_controlled": False},
                    ],
                },
            ],
        },
    ]
    responses.post(
        f"{carbure_client.root_url}api/elec/provision-certificates-qualicharge/bulk-create/",
        status=201,
    )
    carbure_client.bulk_create_certificates(certificates)

    # There was an input data format issue
    responses.post(
        f"{carbure_client.root_url}api/elec/provision-certificates-qualicharge/bulk-create/",
        status=400,
        json={
            "status": "fail",
            "errors": ["Bad format"],
        },
    )
    with pytest.raises(requests.HTTPError, match="400 Client Error: Bad Request"):
        carbure_client.bulk_create_certificates(certificates)

    # There was an unexpected issue
    responses.post(
        f"{carbure_client.root_url}api/elec/provision-certificates-qualicharge/bulk-create/",
        status=500,
    )
    with pytest.raises(
        requests.HTTPError, match="500 Server Error: Internal Server Error"
    ):
        carbure_client.bulk_create_certificates(certificates)
