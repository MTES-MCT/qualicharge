"""QualiCharge API client HTTP module."""

from json import JSONDecodeError

import httpx
from pydantic import ValidationError

from .exceptions import AuthenticationError, ConfigurationError
from .models import Token


class OAuth2AccessToken(httpx.Auth):
    """Add OAuth2 access token to HTTP API requests header."""

    def __init__(self, access_token):
        """Instantiate requests Auth object with generated access_token."""
        self.access_token = access_token

    def auth_flow(self, request):
        """Modify and return the request."""
        request.headers["Authorization"] = f"Bearer {self.access_token}"
        yield request


class HTTPClient(httpx.AsyncClient):
    """QualiChage API HTTP client."""

    def __init__(
        self, *args, username: str, password: str, base_url: str = "", **kwargs
    ):
        """Override default httpx.AsyncClient instantiation to handle authentication."""
        if not base_url:
            raise ConfigurationError(
                "The `base_url` argument should be set to your root API url"
            )

        super().__init__(*args, base_url=base_url, **kwargs)

        self.username: str = username
        self.password: str = password
        self.headers = httpx.Headers({b"Content-Type": b"application/json"})

    def _get_auth(self) -> OAuth2AccessToken:
        """Request OAuth2 access token from the API."""
        response = httpx.post(
            self._merge_url("/auth/token"),
            data={"username": self.username, "password": self.password},
            timeout=10,
        )
        try:
            token = Token(**response.json())
        except JSONDecodeError as exc:
            raise AuthenticationError(
                "Invalid response from the API server with provided credentials"
            ) from exc
        except ValidationError as exc:
            raise AuthenticationError(
                (
                    "Cannot get an access token from the API server with provided "
                    "credentials"
                )
            ) from exc

        return OAuth2AccessToken(token.access_token)

    async def request(self, method, url, **kwargs) -> httpx.Response:
        """Automatically renew access token when expired."""
        # Get access token if it has not been set yet
        if not self._auth:
            self._auth = self._get_auth()

        response = await super().request(method, url, **kwargs)

        # Try to regenerate the access token in case of 401 response
        if response.status_code == httpx.codes.UNAUTHORIZED:
            try:
                json_response = response.json()
            except JSONDecodeError:
                return response

            # Token expired, let's get a new one
            if "Token signature expired" in json_response["message"]:
                self.auth = self._get_auth()
                # Perform the request with the new token
                return await super().request(method, url, **kwargs)

        return response
