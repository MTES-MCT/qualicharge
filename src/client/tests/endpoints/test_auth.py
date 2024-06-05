"""Tests for the qcc.endpoints.auth module."""

import pytest

from qcc.endpoints.auth import Auth


def test_auth_initialization(client):
    """Test the auth endpoint __init__ method."""
    auth = Auth(client)
    assert auth.client == client


@pytest.mark.anyio
async def test_auth_whoami(client, httpx_mock):
    """Test the /auth/whoami endpoint call."""
    auth = Auth(client)

    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/auth/whoami",
        json={"user": "johndoe"},
    )
    assert await auth.whoami() == {"user": "johndoe"}
