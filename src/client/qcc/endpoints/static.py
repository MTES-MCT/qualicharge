"""QualiCharge API client static endpoints."""

import logging
from typing import AsyncIterator, Sequence

import httpx

from qcc.conf import settings
from qcc.exceptions import APIRequestError
from qcc.http import HTTPClient

logger = logging.getLogger(__name__)


class Static:
    """/statique endpoints."""

    def __init__(self, client: HTTPClient) -> None:
        """Set /auth endpoints HTTP client."""
        self.client = client

    async def list(self) -> AsyncIterator[dict]:
        """Query the /statique/ endpoint (GET)."""

        async def get_statiques(url="/statique/"):
            """Get statique items."""
            response = await self.client.get(url)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                raise APIRequestError(response.json()) from err
            json_response = response.json()
            for statique in json_response["items"]:
                yield statique
            if "next" in json_response and json_response["next"]:
                async for statique in get_statiques(json_response["next"]):
                    yield statique

        async for statique in get_statiques():
            yield statique

    async def create(self, statique: dict) -> dict:
        """Query the /statique/ endpoint (POST)."""
        response = await self.client.post("/statique/", json=statique)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        return response.json()

    async def read(self, id_pdc_itinerance: str) -> dict:
        """Query the /statique/{id_pdc_itinerance} endpoint (GET)."""
        response = await self.client.get(f"/statique/{id_pdc_itinerance}")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        return response.json()

    async def update(self, id_pdc_itinerance: str, statique: dict) -> dict:
        """Query the /statique/{id_pdc_itinerance} endpoint (PUT)."""
        response = await self.client.put(
            f"/statique/{id_pdc_itinerance}", json=statique
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        return response.json()

    async def bulk(
        self,
        statiques: Sequence[dict],
        chunk_size: int = settings.API_BULK_CREATE_MAX_SIZE,
        ignore_errors: bool = False,
    ) -> int:
        """Query the /statique/bulk endpoint (POST)."""
        chunk: list = []
        n_created = 0

        async def send_chunk(client, chunk: list[dict]) -> int:
            """Submit a chunk to the API."""
            response = await client.post("/statique/bulk", json=chunk)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                if ignore_errors:
                    logger.debug("Ignored chunk: %s", chunk)
                    logger.warning("Ignored query error: %s", response)
                    return 0
                raise APIRequestError(response.json()) from err
            return response.json()["size"]

        for statique in statiques:
            chunk.append(statique)
            if len(chunk) == chunk_size:
                n_created += await send_chunk(self.client, chunk)
                chunk = []

        if len(chunk):
            n_created += await send_chunk(self.client, chunk)
        return n_created
