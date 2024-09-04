"""QualiCharge API client endpoints base."""

import gzip
import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Sequence

import httpx

from qcc.conf import settings
from qcc.exceptions import APIRequestError
from qcc.http import HTTPClient

logger = logging.getLogger(__name__)


class BaseCreateEndpoint:
    """Base create endpoint."""

    endpoint: str

    def __init__(self, client: HTTPClient) -> None:
        """Set /auth endpoints HTTP client."""
        self.client = client

    async def create(self, obj: dict) -> dict | None:
        """Query the /{endpoint}/ endpoint (POST)."""
        response = await self.client.post(f"{self.endpoint}/", json=obj)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        # Response body may be empty (201)
        if not response.content:
            return None

        return response.json()

    async def bulk(
        self,
        objs: Sequence[dict],
        chunk_size: int = settings.API_BULK_CREATE_MAX_SIZE,
        ignore_errors: bool = False,
    ) -> int:
        """Query the /{endpoint}/bulk endpoint (POST)."""
        chunk: list = []
        n_created = 0

        async def send_chunk(client, chunk: list[dict]) -> int:
            """Submit a chunk to the API."""
            # Zip chunk
            content = gzip.compress(
                json.dumps(chunk).encode("utf-8"),
                compresslevel=settings.GZIP_COMPRESSION_LEVEL,
            )
            response = await client.post(
                f"{self.endpoint}/bulk",
                content=content,
                headers={
                    "Content-Encoding": "gzip",
                    "Content-Type": "application/json",
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                if ignore_errors:
                    logger.debug("Ignored chunk: %s", chunk)
                    logger.warning("Ignored query error: %s", response)
                    return 0
                raise APIRequestError(response.json()) from err
            return response.json()["size"]

        for obj in objs:
            chunk.append(obj)
            if len(chunk) == chunk_size:
                n_created += await send_chunk(self.client, chunk)
                chunk = []

        if len(chunk):
            n_created += await send_chunk(self.client, chunk)
        return n_created


class BaseEndpoint(ABC, BaseCreateEndpoint):
    """Base endpoint CRUD actions."""

    @abstractmethod
    def list(self) -> AsyncIterator[dict]:
        """Query the /{endpoint}/ endpoint (GET)."""

    async def read(self, id_: str) -> dict:
        """Query the /{endpoint}/{id_} endpoint (GET)."""
        response = await self.client.get(f"{self.endpoint}/{id_}")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        return response.json()
