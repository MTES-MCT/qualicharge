"""QualiCharge dynamic models tests."""

from datetime import datetime, timedelta, timezone

import pytest

from qualicharge.conf import settings
from qualicharge.factories.dynamic import SessionCreateFactory, StatusCreateFactory
from qualicharge.models.dynamic import SessionCreate, StatusCreate


def test_session_create_factory():
    """Test the dynamic SessionCreate model factory."""
    session = SessionCreateFactory.build()
    now = datetime.now(tz=timezone.utc)

    assert session.start < now
    assert session.end < now


def test_session_create_model_start_end_consistency():
    """Test the dynamic SessionCreate model: start/end consistency."""
    now = datetime.now(tz=timezone.utc)

    with pytest.raises(ValueError, match="A session cannot start after it has ended."):
        SessionCreate(
            id_pdc_itinerance="FRFASE3300405",
            start=now - timedelta(days=5),
            end=now - timedelta(days=6),
            energy=12.0,
        )


def test_session_create_model_start_max_age():
    """Test the dynamic SessionCreate model: start max age."""
    now = datetime.now(tz=timezone.utc)

    with pytest.raises(ValueError, match="is older than 365 days"):
        SessionCreate(
            id_pdc_itinerance="FRFASE3300405",
            start=now - timedelta(seconds=settings.API_MAX_SESSION_AGE + 3600),
            end=now - timedelta(days=4),
            energy=12.0,
        )


def test_status_create_factory():
    """Test the dynamic StatusCreate model factory."""
    status = StatusCreateFactory.build()

    assert status.horodatage < datetime.now(tz=timezone.utc)


def test_status_create_model():
    """Test the dynamic StatusCreate model."""
    now = datetime.now(tz=timezone.utc)
    base = StatusCreateFactory.build()

    with pytest.raises(ValueError, match="is older than 1 day"):
        StatusCreate(
            **base.model_dump(exclude={"horodatage"}),
            horodatage=now - timedelta(seconds=settings.API_MAX_STATUS_AGE + 3600),
        )
