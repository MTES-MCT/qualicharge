"""Tests for QualiCharge database connection."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


def test_database_connection(db_session):
    """Test the PostgreSQL database connection."""
    try:
        db_session.execute(text("SELECT 42 as life"))
    except OperationalError:
        pytest.fail("Cannot connect to configured database")
