"""Tests for the QualiCharge API root routes."""

from fastapi import status


def test_whoami_not_auth(client):
    """Test the whoami endpoint when user is not authenticated."""
    response = client.get("/whoami")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}


def test_whoami_auth(client_auth):
    """Test the whoami endpoint when user is authenticated."""
    response = client_auth.get("/whoami")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"email": "john@doe.com"}
