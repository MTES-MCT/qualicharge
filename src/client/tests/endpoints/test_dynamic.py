"""Tests for the qcc.endpoints.dynamic module."""

from datetime import datetime

import pytest

from qcc.endpoints.dynamic import Session, Status
from qcc.exceptions import APIRequestError


def test_dynamic_status_initialization(client):
    """Test the Status endpoint __init__ method."""
    status = Status(client)
    assert status.client == client


@pytest.mark.anyio
async def test_dynamic_status_list(client, httpx_mock):
    """Test the /dynamique/status/ endpoint call."""
    status = Status(client)

    # No parameters
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/",
        json=list(range(0, 10)),
    )
    assert [item async for item in status.list()] == list(range(0, 10))

    # Filter: from_
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?from=2024-06-13T12%3A02%3A33",
        json=list(range(0, 2)),
    )
    assert [
        item async for item in status.list(from_=datetime(2024, 6, 13, 12, 2, 33))
    ] == list(range(0, 2))

    # Filter: charge points
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?pdc=FR911E1111ER1",
        json=list(range(2, 5)),
    )
    assert [item async for item in status.list(pdc=["FR911E1111ER1"])] == list(
        range(2, 5)
    )
    # Filter: multiple charge points
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?pdc=FR911E1111ER1&pdc=FR911E1111ER2",
        json=list(range(1, 3)),
    )
    assert [
        item async for item in status.list(pdc=["FR911E1111ER1", "FR911E1111ER2"])
    ] == list(range(1, 3))

    # Filter: stations
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?station=FR911P0001",
        json=list(range(5, 10)),
    )
    assert [item async for item in status.list(station=["FR911P0001"])] == list(
        range(5, 10)
    )

    # Filter: stations + from_
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?station=FR911P0001&from=2024-06-13T12%3A02%3A33",
        json=list(range(2, 8)),
    )
    assert [
        item
        async for item in status.list(
            station=["FR911P0001"], from_=datetime(2024, 6, 13, 12, 2, 33)
        )
    ] == list(range(2, 8))

    # Raise an HTTP 500 error
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/",
        status_code=500,
        json={"message": "An unknown error occured."},
    )
    with pytest.raises(APIRequestError, match="An unknown error occured"):
        assert await anext(status.list())


@pytest.mark.anyio
async def test_dynamic_status_read(client, httpx_mock):
    """Test the /dynamique/status/{id_pdc_itinerance} endpoint call."""
    status = Status(client)

    id_pdc_itinerance = "FRS63E0001"
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/dynamique/status/{id_pdc_itinerance}",
        json={"id_pdc_itinerance": id_pdc_itinerance},
    )
    assert await status.read(id_pdc_itinerance) == {
        "id_pdc_itinerance": id_pdc_itinerance
    }

    # API error
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/dynamique/status/{id_pdc_itinerance}",
        status_code=404,
        json={"message": "Selected point of charge does not have status record yet"},
    )
    with pytest.raises(
        APIRequestError,
        match="Selected point of charge does not have status record yet",
    ):
        await status.read(id_pdc_itinerance)


@pytest.mark.anyio
async def test_dynamic_status_history(client, httpx_mock):
    """Test the /dynamique/status/{id_pdc_itinerance}/history endpoint call."""
    status = Status(client)

    id_pdc_itinerance = "FRS63E0001"
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/dynamique/status/{id_pdc_itinerance}/history",
        json=list(range(10)),
    )
    assert [item async for item in status.history(id_pdc_itinerance)] == list(range(10))

    # API error
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/dynamique/status/{id_pdc_itinerance}/history",
        status_code=404,
        json={"message": "Selected point of charge does not have status record yet"},
    )
    with pytest.raises(
        APIRequestError,
        match="Selected point of charge does not have status record yet",
    ):
        assert await anext(status.history(id_pdc_itinerance))


@pytest.mark.anyio
async def test_dynamic_status_create(client, httpx_mock):
    """Test the /dynamique/status endpoint call."""
    status = Status(client)

    data = {"id_pdc_itinerance": "FRS63E0001"}
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/",
        status_code=201,
    )
    assert await status.create(data) is None

    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/",
        status_code=404,
        json={"message": "Attached point of charge does not exist"},
    )
    with pytest.raises(
        APIRequestError, match="Attached point of charge does not exist"
    ):
        assert await status.create(data)


@pytest.mark.anyio
async def test_dynamic_status_bulk(client, httpx_mock):
    """Test the /dynamique/status/bulk endpoint call."""
    status = Status(client)

    # total % chunk_size == 0
    total = 30
    statuses = [{"id_pdc_itinerance": f"FRS63E00{x:02d}"} for x in range(total)]
    for chunk_size in (5, 6, 10):
        httpx_mock.add_response(
            method="POST",
            url="http://example.com/api/v1/dynamique/status/bulk",
            json={"size": chunk_size},
        )
        assert await status.bulk(statuses, chunk_size=chunk_size) == total

    # total % chunk_size == 2
    total = 12
    statuses = [{"id_pdc_itinerance": f"FRS63E00{x:02d}"} for x in range(total)]
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        json={"size": 10},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        json={"size": 2},
    )
    assert await status.bulk(statuses, chunk_size=10) == total

    # API Errors
    total = 7
    statuses = [{"id_pdc_itinerance": f"FRS63E00{x:02d}"} for x in range(total)]
    chunk_size = 5
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        status_code=500,
        json={"message": "Invalid data"},
    )
    with pytest.raises(APIRequestError, match="Invalid data"):
        await status.bulk(statuses, chunk_size=chunk_size)

    # Ignore errors
    assert await status.bulk(statuses, chunk_size=chunk_size, ignore_errors=True) == 0

    # What if an error occurs for the second chunk?
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        json={"size": chunk_size},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        status_code=500,
        json={"message": "Invalid data"},
    )
    assert (
        await status.bulk(statuses, chunk_size=chunk_size, ignore_errors=True)
        == chunk_size
    )


@pytest.mark.anyio
async def test_dynamic_session_create(client, httpx_mock):
    """Test the /dynamique/session endpoint call."""
    session = Session(client)

    data = {"id_pdc_itinerance": "FRS63E0001"}
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/",
        status_code=201,
    )
    assert await session.create(data) is None

    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/",
        status_code=404,
        json={"message": "Attached point of charge does not exist"},
    )
    with pytest.raises(
        APIRequestError, match="Attached point of charge does not exist"
    ):
        assert await session.create(data)


@pytest.mark.anyio
async def test_dynamic_session_bulk(client, httpx_mock):
    """Test the /dynamique/session/bulk endpoint call."""
    session = Session(client)

    # total % chunk_size == 0
    total = 30
    sessions = [{"id_pdc_itinerance": f"FRS63E00{x:02d}"} for x in range(total)]
    for chunk_size in (5, 6, 10):
        httpx_mock.add_response(
            method="POST",
            url="http://example.com/api/v1/dynamique/session/bulk",
            json={"size": chunk_size},
        )
        assert await session.bulk(sessions, chunk_size=chunk_size) == total

    # total % chunk_size == 2
    total = 12
    sessions = [{"id_pdc_itinerance": f"FRS63E00{x:02d}"} for x in range(total)]
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/bulk",
        json={"size": 10},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/bulk",
        json={"size": 2},
    )
    assert await session.bulk(sessions, chunk_size=10) == total

    # API Errors
    total = 7
    sessions = [{"id_pdc_itinerance": f"FRS63E00{x:02d}"} for x in range(total)]
    chunk_size = 5
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/bulk",
        status_code=500,
        json={"message": "Invalid data"},
    )
    with pytest.raises(APIRequestError, match="Invalid data"):
        await session.bulk(sessions, chunk_size=chunk_size)

    # Ignore errors
    assert await session.bulk(sessions, chunk_size=chunk_size, ignore_errors=True) == 0

    # What if an error occurs for the second chunk?
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/bulk",
        json={"size": chunk_size},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/bulk",
        status_code=500,
        json={"message": "Invalid data"},
    )
    assert (
        await session.bulk(sessions, chunk_size=chunk_size, ignore_errors=True)
        == chunk_size
    )
