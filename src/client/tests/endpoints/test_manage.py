"""Tests for the qcc.endpoints.dynamic module."""

from datetime import datetime

import pytest

from qcc.endpoints.manage import Manage
from qcc.exceptions import APIRequestError


def test_manage_initialization(client):
    """Test the Status endpoint __init__ method."""
    manage = Manage(client)
    assert manage.client == client


@pytest.mark.anyio
async def test_manage_read_stations(client, httpx_mock):
    """Test the /manage/station/siren/{siren} endpoint call."""
    manage = Manage(client)

    # No parameters
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/manage/station/siren/123456789",
        json=list(range(0, 10)),
    )
    assert [item async for item in manage.read_stations("123456789")] == list(
        range(0, 10)
    )

    # Filter: after
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/manage/station/siren/123456789?after=2024-06-13T12%3A02%3A33",
        json=list(range(0, 2)),
    )
    assert [
        item
        async for item in manage.read_stations(
            "123456789", after=datetime(2024, 6, 13, 12, 2, 33)
        )
    ] == list(range(0, 2))

    # Raise an HTTP 500 error
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/manage/station/siren/123456789",
        status_code=500,
        json={"message": "An unknown error occured."},
    )
    with pytest.raises(APIRequestError, match="An unknown error occured"):
        assert await anext(manage.read_stations("123456789"))

    # No station found
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/manage/station/siren/123456789",
        status_code=404,
        json={"message": "No station found."},
    )
    with pytest.raises(APIRequestError, match="No station found."):
        assert await anext(manage.read_stations("123456789"))
