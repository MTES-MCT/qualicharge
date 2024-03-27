"""Tests for the QualiCharge API."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from qualicharge.api import app


def test_hello():
    """Test the hello word example."""
    client = TestClient(app)
    response = client.get("/api/v1/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Hello world."}


def test_database_connection(db_session):
    """Test the PostgreSQL database connection."""
    try:
        db_session.execute(text("SELECT 42 as life"))
    except OperationalError:
        pytest.fail("Cannot connect to configured database")
