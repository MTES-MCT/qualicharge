"""QualiCharge API client tariff endpoints."""

from datetime import datetime
from typing import AsyncIterator, List, Optional

import httpx

from qcc.endpoints.base import BaseEndpoint

from ..exceptions import APIRequestError


class Tariff(BaseEndpoint):
    """/statique/tariff endpoints."""

    endpoint: str = "/statique/tariff"

    async def list(
        self,
        from_: Optional[datetime] = None,
        to: Optional[datetime] = None,
        pdc: Optional[List[str]] = None,
        current: Optional[bool] = None,
    ) -> AsyncIterator[dict]:
        """Query the /statique/tariff endpoint (GET)."""
        from_str = from_.isoformat() if from_ else None
        to_str = to.isoformat() if to else None
        params = dict(
            p
            for p in (
                ("from", from_str),
                ("to", to_str),
                ("pdc", pdc),
                ("current", current),
            )
            if p[1] is not None
        )

        response = await self.client.get(f"{self.endpoint}/", params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        for tariff in response.json()["items"]:
            yield tariff

    async def applicable(
        self,
        id_pdc_itinerance: str,
        at: Optional[datetime] = None,
    ) -> dict:
        """Query the /statique/{id_pdc_itinerance}/tariff endpoint."""
        params = {"at": at.isoformat()} if at else {}
        response = await self.client.get(
            f"/statique/{id_pdc_itinerance}/tariff",
            params=params,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise APIRequestError(response.json()) from err

        return response.json()
