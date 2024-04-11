"""QualiCharge dynamic models tests."""

from datetime import datetime

from qualicharge.factories.dynamic import SessionFactory, StatusFactory


def test_session_model():
    """Test the dynamic Session model."""
    session = SessionFactory.build()

    assert session.start < datetime.now()
    assert session.end < datetime.now()


def test_status_model():
    """Test the dynamic Status model."""
    status = StatusFactory.build()

    assert status.horodatage < datetime.now()
