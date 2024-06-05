"""QualiCharge API client auth endpoints."""

from qcc.http import HTTPClient


class Auth:
    """/auth endpoints."""

    def __init__(self, client: HTTPClient) -> None:
        """Set /auth endpoints HTTP client."""
        self.client = client

    async def whoami(self) -> dict:
        """Query the /whoami endpoint."""
        response = await self.client.get("/auth/whoami")
        return response.json()
