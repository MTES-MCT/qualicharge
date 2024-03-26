"""Tests for the QualiCharge API."""

from fastapi import status
from fastapi.testclient import TestClient

from qualicharge.api import app

client = TestClient(app)


def test_hello():
    """Test the hello word example."""
    response = client.get("/api/v1/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Hello world."}
