"""QualiCharge dynamic models tests."""

from datetime import datetime

from qualicharge.factories.dynamic import SessionCreateFactory, StatusCreateFactory


def test_session_create_model():
    """Test the dynamic SessionCreate model."""
    session = SessionCreateFactory.build()

    assert session.start < datetime.now()
    assert session.end < datetime.now()


def test_status_create_model():
    """Test the dynamic StatusCreate model."""
    status = StatusCreateFactory.build()

    assert status.horodatage < datetime.now()
