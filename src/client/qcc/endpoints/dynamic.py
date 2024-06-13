"""QualiCharge API client dynamic endpoints."""

import logging
from datetime import datetime
from typing import AsyncIterator, List, Optional

import httpx

from qcc.endpoints.base import BaseCreateEndpoint

from ..exceptions import APIRequestError
from .base import BaseEndpoint

logger = logging.getLogger(__name__)


class Status(BaseEndpoint):
    """/dynamique/status endpoints."""

    endpoint: str = "/dynamique/status"

    async def list(
        self,
        from_: Optional[datetime] = None,
        pdc: Optional[List[str]] = None,
        station: Optional[List[str]] = None,
    ) -> AsyncIterator[dict]:
        """Query the /dynamique/status endpoint (GET)."""
        # Get isotring for the `from_` parameter
        from_str = from_.isoformat() if from_ else None

        # Query filters
        params = dict(
            p
            for p in (("from", from_str), ("pdc", pdc), ("station", station))
            if p[1] is not None
        )

        response = await self.client.get(f"{self.endpoint}/", params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        for status in response.json():
            yield status

    async def history(
        self, id_: str, from_: Optional[datetime] = None
    ) -> AsyncIterator[dict]:
        """Query the /{endpoint}/{id_}/history endpoint (GET)."""
        # Get isotring for the `from_` parameter
        from_str = from_.isoformat() if from_ else None
        params = {"from": from_str} if from_str else {}

        response = await self.client.get(
            f"{self.endpoint}/{id_}/history", params=params
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        for status in response.json():
            yield status


class Session(BaseCreateEndpoint):
    """/dynamique/session endpoints."""

    endpoint: str = "/dynamique/session"
