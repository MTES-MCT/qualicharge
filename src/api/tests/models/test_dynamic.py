"""QualiCharge dynamic models tests."""

from datetime import datetime

from qualicharge.factories.dynamic import StatusFactory


def test_status_model():
    """Test the dynamic Status model."""
    status = StatusFactory.build()

    assert status.horodatage < datetime.now()
