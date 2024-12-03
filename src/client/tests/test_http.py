"""Tests for the qcc.http module."""

import httpx
import pytest

from qcc.exceptions import AuthenticationError, ConfigurationError
from qcc.http import HTTPClient, OAuth2AccessToken

# ruff: noqa: S105, S106


def test_client_init(httpx_mock):
    """Test the HTTPClient instantiation."""
    httpx_mock.add_response(
        method="POST", json={"access_token": "foo", "token_type": "bearer"}
    )

    with pytest.raises(
        TypeError,
        match="missing 2 required keyword-only arguments: 'username' and 'password'",
    ):
        HTTPClient()

    with pytest.raises(
        ConfigurationError,
        match="The `base_url` argument should be set to your root API url",
    ):
        HTTPClient(username="johndoe", password="fake")

    # We do not login during instantiation
    client = HTTPClient(username="johndoe", password="fake", base_url="http://fake")
    assert client._auth is None

    # Explicit login
    client = HTTPClient(username="johndoe", password="fake", base_url="http://fake")
    client._auth = client._get_auth()
    assert isinstance(client._auth, OAuth2AccessToken)
    assert client._auth.access_token == "foo"


def test_client_get_auth_with_invalid_api_response(httpx_mock):
    """Test the HTTPClient get_auth method when API response is not valid."""
    client = HTTPClient(username="johndoe", password="fake", base_url="http://fake")

    # response body is not a valid JSON
    httpx_mock.add_response(method="POST", text="Oops")
    with pytest.raises(
        AuthenticationError,
        match=("Invalid response from the API server with provided credentials"),
    ):
        client._get_auth()

    # token_type is missing in the response
    httpx_mock.add_response(method="POST", json={"access_token": "foo"})
    with pytest.raises(
        AuthenticationError,
        match=(
            "Cannot get an access token from the API server with provided credentials"
        ),
    ):
        client._get_auth()


@pytest.mark.anyio
async def test_client_unauthorized_request(httpx_mock):
    """Test client request when the API server returns a 401 status code."""
    httpx_mock.add_response(
        method="POST", json={"access_token": "foo", "token_type": "bearer"}
    )
    client = HTTPClient(username="johndoe", password="fake", base_url="http://fake")

    httpx_mock.add_response(method="GET", status_code=401, text="Oops")
    response = await client.get("/auth/whoami")
    assert response.status_code == httpx.codes.UNAUTHORIZED
    # Response has not been modified
    assert response.content == b"Oops"


@pytest.mark.anyio
@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
async def test_client_expired_token_renewal(httpx_mock):
    """Test client request when the access token expired."""
    httpx_mock.add_response(
        method="POST", json={"access_token": "foo", "token_type": "bearer"}
    )
    client = HTTPClient(username="johndoe", password="fake", base_url="http://fake")

    httpx_mock.add_response(
        method="GET",
        status_code=401,
        json={"message": "Authentication failed: Token signature expired"},
    )
    httpx_mock.add_response(
        method="GET",
        status_code=200,
        json={"fake": 1},
    )
    response = await client.get("/auth/whoami")
    assert response.status_code == httpx.codes.OK
    assert response.content == b'{"fake":1}'

    # Check requests
    requests = httpx_mock.get_requests()
    assert requests[0].method == "POST"  # first token
    assert requests[1].method == "GET"  # 401: token expired
    assert requests[2].method == "POST"  # second (new) token
    assert requests[3].method == "GET"  # 200: valid request
