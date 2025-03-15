"""Dashboard core qualicharge clients."""

import asyncio
from datetime import datetime
from typing import Optional

from django.conf import settings
from qcc.client import QCC

from apps.core.qualicharge_api.adapters import ManageStationsAdapter


class QualiChargeApi:
    """Facade class to simplify usage of the QualiCharge API."""

    def __init__(self):
        """Initialize the clients."""
        self.manage_station_client = ManageStationClient()

    def manage_stations_list(
        self, siren: str, after: Optional[datetime] = None
    ) -> list[ManageStationsAdapter]:
        """Get station information from a SIREN number."""
        return asyncio.run(self.manage_station_client.list(siren, after))


class QualiChargeBaseClient:
    """Base Client for `QualiCharge` API.

    Based on qcc.client.QCC
    """

    def __init__(self):
        """Initialize the API client."""
        self.username = settings.QCC_API_LOGIN_USERNAME
        self.password = settings.QCC_API_LOGIN_PASSWORD
        self.api_root_url = settings.QCC_API_ROOT_URL
        self.client = QCC(self.username, self.password, self.api_root_url)


class ManageStationClient(QualiChargeBaseClient):
    """Client for the `manage/station` endpoint."""

    async def list(
        self, siren: str, after: Optional[datetime] = None
    ) -> list[ManageStationsAdapter]:
        """Retrieves company information from the SIREN and adapts it."""
        return [
            ManageStationsAdapter.from_api_response(station)
            async for station in self.client.manage.read_stations(siren, after)
        ]
