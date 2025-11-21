"""QualiCharge prefect indicators: tiruert.

CARBURE integration utils.
"""

import logging
from typing import List, Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, EmailStr, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class CarbureAPIUser(BaseModel):
    """Carbure user."""

    email: EmailStr
    password: str
    api_key: str


class CarbureAPISettings(BaseSettings):
    """Settings for the Carbure API."""

    model_config = SettingsConfigDict(
        env_prefix="CARBURE_",
        env_nested_delimiter="__",
    )

    root_url: HttpUrl
    user: CarbureAPIUser


class CarbureClient:
    """Carbure API client."""

    def __init__(self, config: CarbureAPISettings) -> None:
        """Set up Carbure API client."""
        self.root_url = config.root_url
        self.user = config.user
        self.session = requests.Session()
        self.session.headers = {
            "Accept": "application/json",
            "X-Api-Key": self.user.api_key,
        }
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def _api_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[dict | List[dict]] = None,
    ) -> dict | List[dict] | None:
        """Perform an API request."""
        url = urljoin(str(self.root_url), endpoint)

        # Perform the request
        response = getattr(self.session, method)(url, json=payload)

        # User is not authenticated.
        # Perform authentication and perform the request one more time.
        if response.status_code in (
            requests.codes.forbidden,
            requests.codes.unauthorized,
        ):
            self._auth()
            return self._api_request(method, endpoint, payload)
        # Request seems not satisfying: display error logs before raising an exception
        elif response.status_code not in (requests.codes.ok, requests.codes.created):
            logger.error(f"[HTTP {response.status_code}] {response.text}")

        response.raise_for_status()
        return response.json() if response.text else None

    def _auth(self) -> None:
        """Authenticate to the Carbure API."""
        if self.refresh_token is not None:
            tokens = self._api_request(
                "post", "/api/token/refresh/", {"refresh": self.refresh_token}
            )
        else:
            tokens = self._api_request(
                "post", "/api/token/", self.user.model_dump(exclude={"api_key"})
            )
            self.refresh_token = tokens["refresh"]
        self.access_token = tokens["access"]
        self.session.headers |= {"Authorization": f"Bearer {self.access_token}"}

    def check_entities(self) -> List[dict]:
        """Check Carbure registered entities."""
        return self._api_request("get", "/api/resources/entities")

    def bulk_create_certificates(self, certificates: List[dict]) -> None:
        """Bulk create elec provision certificates."""
        self._api_request(
            "post",
            "/api/elec/provision-certificates-qualicharge/bulk-create/",
            certificates,
        )
