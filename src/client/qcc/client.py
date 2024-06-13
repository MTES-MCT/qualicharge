"""QualiCharge API client."""

from .endpoints.auth import Auth
from .endpoints.dynamic import Session, Status
from .endpoints.static import Static
from .exceptions import ConfigurationError
from .http import HTTPClient


class QCC:
    """QualiCharge API client."""

    def __init__(
        self,
        username: str,
        password: str,
        api_root_url: str,
    ) -> None:
        """Register all supported endpoints."""
        if any(not arg for arg in (username, password, api_root_url)):
            raise ConfigurationError(
                "API credentials are not set in client nor settings"
            )

        self.client = HTTPClient(
            username=username, password=password, base_url=api_root_url
        )
        self.auth = Auth(self.client)
        self.static = Static(self.client)
        self.status = Status(self.client)
        self.session = Session(self.client)
