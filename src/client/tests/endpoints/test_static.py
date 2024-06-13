"""Tests for the qcc.endpoints.static module."""

import pytest

from qcc.endpoints.static import Static
from qcc.exceptions import APIRequestError


def test_static_initialization(client):
    """Test the static endpoint __init__ method."""
    static = Static(client)
    assert static.client == client


@pytest.mark.anyio
async def test_static_list(client, httpx_mock):
    """Test the /statique endpoint call."""
    static = Static(client)

    # No pagination
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/",
        json={"items": list(range(0, 10))},
    )
    assert [item async for item in static.list()] == list(range(0, 10))

    # Paginate
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/",
        json={
            "items": list(range(0, 10)),
            "next": "http://example.com/api/v1/statique/?offset=10&limit=10",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/?offset=10&limit=10",
        json={"items": list(range(10, 20)), "next": None},
    )
    assert [item async for item in static.list()] == list(range(0, 20))

    # API errors
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/",
        status_code=500,
        json={"message": "An unknown error occured."},
    )
    with pytest.raises(APIRequestError, match="An unknown error occured"):
        assert await anext(static.list())


@pytest.mark.anyio
async def test_static_create(client, httpx_mock):
    """Test the /statique/ POST endpoint call."""
    static = Static(client)

    statique = {"id_pdc_itinerance": "FRS63E0001"}
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/",
        json=statique,
    )
    assert await static.create(statique) == statique

    # API errors
    statique = {"id_pdc_itinerance": "FRS63E0001"}
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/",
        status_code=422,
        json={"message": "Validation error!"},
    )
    with pytest.raises(APIRequestError, match="Validation error!"):
        await static.create(statique)


@pytest.mark.anyio
async def test_static_read(client, httpx_mock):
    """Test the /statique/{id_pdc_itinerance} endpoint call."""
    static = Static(client)

    id_pdc_itinerance = "FRS63E0001"
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}",
        json={"id_pdc_itinerance": id_pdc_itinerance},
    )
    assert await static.read(id_pdc_itinerance) == {
        "id_pdc_itinerance": id_pdc_itinerance
    }

    # API errors
    id_pdc_itinerance = "FRS63E0001"
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}",
        status_code=500,
        json={"message": "Authentication required"},
    )
    with pytest.raises(APIRequestError, match="Authentication required"):
        await static.read(id_pdc_itinerance)


@pytest.mark.anyio
async def test_static_update(client, httpx_mock):
    """Test the /statique/{id_pdc_itinerance} PUT endpoint call."""
    static = Static(client)

    id_pdc_itinerance = "FRS63E0001"
    statique = {"id_pdc_itinerance": "FRS63E0001"}
    httpx_mock.add_response(
        method="PUT",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}",
        json=statique,
    )
    assert await static.update(id_pdc_itinerance, statique) == {
        "id_pdc_itinerance": id_pdc_itinerance
    }

    # API errors
    id_pdc_itinerance = "FRS63E0001"
    statique = {"id_pdc_itinerance": "FRS63E0001"}
    httpx_mock.add_response(
        method="PUT",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}",
        status_code=422,
        json={"message": "Invalid format"},
    )
    with pytest.raises(APIRequestError, match="Invalid format"):
        await static.update(id_pdc_itinerance, statique)


@pytest.mark.anyio
async def test_static_bulk(client, httpx_mock):
    """Test the /statique/bulk endpoint call."""
    static = Static(client)

    # total % chunk_size == 0
    total = 30
    statiques = [{"id_pdc_itinerance": f"FRS63E00{x:02d}"} for x in range(total)]
    for chunk_size in (5, 6, 10):
        httpx_mock.add_response(
            method="POST",
            url="http://example.com/api/v1/statique/bulk",
            json={"size": chunk_size},
        )
        assert await static.bulk(statiques, chunk_size=chunk_size) == total

    # total % chunk_size == 2
    total = 12
    statiques = [{"id_pdc_itinerance": f"FRS63E00{x:02d}"} for x in range(total)]
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/bulk",
        json={"size": 10},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/bulk",
        json={"size": 2},
    )
    assert await static.bulk(statiques, chunk_size=10) == total

    # API errors
    total = 7
    statiques = [{"id_pdc_itinerance": f"FRS63E00{x:02d}"} for x in range(total)]
    chunk_size = 5
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/bulk",
        status_code=500,
        json={"message": "Invalid data"},
    )
    with pytest.raises(APIRequestError, match="Invalid data"):
        await static.bulk(statiques, chunk_size=chunk_size)

    # Ignore errors
    assert await static.bulk(statiques, chunk_size=chunk_size, ignore_errors=True) == 0

    # What if an error occurs for the second chunk?
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/bulk",
        json={"size": chunk_size},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/bulk",
        status_code=500,
        json={"message": "Invalid data"},
    )
    assert (
        await static.bulk(statiques, chunk_size=chunk_size, ignore_errors=True)
        == chunk_size
    )
