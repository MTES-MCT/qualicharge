"""QualiCharge API client dynamic endpoints."""

import logging
from datetime import datetime
from typing import AsyncIterator, Optional

import httpx

from qcc.http import HTTPClient

from ..exceptions import APIRequestError

logger = logging.getLogger(__name__)


class Manage:
    """/manage endpoints."""

    endpoint: str = "/manage"

    def __init__(self, client: HTTPClient) -> None:
        """Set /auth endpoints HTTP client."""
        self.client = client

    async def read_stations(
        self,
        siren: str,
        after: Optional[datetime] = None,
    ) -> AsyncIterator[dict]:
        """Query the /dynamique/status endpoint (GET)."""
        # Get ISO string for the `after` parameter
        after_str = after.isoformat() if after else None

        # Query filters
        params = dict(p for p in (("after", after_str),) if p[1] is not None)

        url = f"{self.endpoint}/station/siren/{siren}"
        response = await self.client.get(url, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        for station in response.json():
            yield station
