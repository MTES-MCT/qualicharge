"""Dashboard consent configuration tests."""

import datetime

import pytest
from django.utils import timezone

FAKE_TIME = datetime.datetime(2025, 1, 6, 17, 5, 55, 0, tzinfo=datetime.timezone.utc)


@pytest.fixture
def patch_datetime_now(monkeypatch):
    """Monkeypatch datetime.datetime.now to return a frozen date (`FAKE_TIME`)."""

    class FakeDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=datetime.timezone.utc):
            return FAKE_TIME

    monkeypatch.setattr(datetime, "datetime", FakeDatetime)


@pytest.fixture
def patch_timezone_now(monkeypatch):
    """Monkeypatch timezone.now to return a frozen date (`FAKE_TIME`)."""

    def mock_now():
        return FAKE_TIME

    monkeypatch.setattr(timezone, "now", mock_now)
