"""QualiCharge API client static endpoints."""

import logging
from typing import AsyncIterator

import httpx

from ..exceptions import APIRequestError
from .base import BaseEndpoint

logger = logging.getLogger(__name__)


class Static(BaseEndpoint):
    """/statique endpoints."""

    endpoint: str = "/statique"

    async def list(self) -> AsyncIterator[dict]:
        """Query the /statique/ endpoint (GET)."""

        async def get_statiques(url=f"{self.endpoint}/"):
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

    async def update(self, id_: str, obj: dict) -> dict:
        """Query the /{endpoint}/{id_} endpoint (PUT)."""
        response = await self.client.put(f"{self.endpoint}/{id_}", json=obj)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        return response.json()
