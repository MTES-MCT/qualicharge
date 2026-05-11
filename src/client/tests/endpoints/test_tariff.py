"""Tests for the qcc.endpoints.tariff module."""

from datetime import datetime

import pytest

from qcc.endpoints.tariff import Tariff
from qcc.exceptions import APIRequestError


def test_tariff_initialization(client):
    """Test the tariff endpoint __init__ method."""
    tariff = Tariff(client)
    assert tariff.client == client


@pytest.mark.anyio
async def test_tariff_list(client, httpx_mock):
    """Test the /statique/tariff/ endpoint call."""
    tariff = Tariff(client)

    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/tariff/",
        json=list(range(0, 10)),
    )
    assert [item async for item in tariff.list()] == list(range(0, 10))

    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/tariff/?from=2026-02-23T10%3A00%3A00&to=2026-02-24T10%3A00%3A00&pdc=FRS63E0001",
        json=list(range(0, 2)),
    )
    assert [
        item
        async for item in tariff.list(
            from_=datetime(2026, 2, 23, 10),
            to=datetime(2026, 2, 24, 10),
            pdc=["FRS63E0001"],
        )
    ] == list(range(0, 2))

    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/tariff/",
        status_code=500,
        json={"message": "An unknown error occured."},
    )
    with pytest.raises(APIRequestError, match="An unknown error occured"):
        assert await anext(tariff.list())


@pytest.mark.anyio
async def test_tariff_create(client, httpx_mock):
    """Test the /statique/tariff/ create endpoint call."""
    tariff = Tariff(client)
    data = {"raw": {"id": "t1", "elements": []}}

    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/tariff/",
        json={"id": "tariff-id"},
    )
    assert await tariff.create(data) == {"id": "tariff-id"}


@pytest.mark.anyio
async def test_tariff_read(client, httpx_mock):
    """Test the /statique/tariff/{id} endpoint call."""
    tariff = Tariff(client)
    tariff_id = "4db7b976-faf4-4833-9728-a0bbf3bdf5fe"

    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/statique/tariff/{tariff_id}",
        json={"id": tariff_id},
    )
    assert await tariff.read(tariff_id) == {"id": tariff_id}


@pytest.mark.anyio
async def test_tariff_delete(client, httpx_mock):
    """Test the /statique/tariff/{id} DELETE endpoint call."""
    tariff = Tariff(client)
    tariff_id = "4db7b976-faf4-4833-9728-a0bbf3bdf5fe"

    httpx_mock.add_response(
        method="DELETE",
        url=f"http://example.com/api/v1/statique/tariff/{tariff_id}",
        status_code=204,
    )
    assert await tariff.delete(tariff_id) is None


@pytest.mark.anyio
async def test_tariff_applicable(client, httpx_mock):
    """Test the /statique/{id_pdc_itinerance}/tariff endpoint call."""
    tariff = Tariff(client)
    id_pdc_itinerance = "FRS63E0001"

    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}/tariff",
        json={"id_pdc_itinerance": id_pdc_itinerance},
    )
    assert await tariff.applicable(id_pdc_itinerance) == {
        "id_pdc_itinerance": id_pdc_itinerance
    }

    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}/tariff?at=2026-02-23T10%3A00%3A00",
        json={"id_pdc_itinerance": id_pdc_itinerance},
    )
    assert await tariff.applicable(
        id_pdc_itinerance,
        at=datetime(2026, 2, 23, 10),
    ) == {"id_pdc_itinerance": id_pdc_itinerance}


@pytest.mark.anyio
async def test_tariff_associate(client, httpx_mock):
    """Test the /statique/pointdechargetariff endpoint call."""
    tariff = Tariff(client)
    data = {"original_id": "t1", "id_pdc_itinerance": ["FRS63E0001"]}

    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/pointdechargetariff",
        json={"id": "tariff-id"},
    )
    assert await tariff.associate(data) == {"id": "tariff-id"}
