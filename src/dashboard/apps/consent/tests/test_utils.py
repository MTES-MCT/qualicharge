"""Dashboard consent utils tests."""

import datetime

import pytest

from apps.consent.utils import consent_end_date, consent_start_date


@pytest.mark.django_db
def test_consent_start_date_current_year(patch_datetime_now):
    """Test `consent_start_date` returns the start date of the current year."""
    start_date = consent_start_date()
    current_year = datetime.datetime.now().year
    expected_date = datetime.datetime(year=current_year, month=1, day=1)
    assert start_date == expected_date


@pytest.mark.django_db
def test_consent_end_date_with_days(patch_datetime_now):
    """Test `consent_end_date` function when days argument is provided."""
    days = 10
    end_date = consent_end_date(days=days)
    expected_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=days
    )
    assert end_date == expected_date


@pytest.mark.django_db
def test_consent_end_date_without_days(patch_datetime_now):
    """Test `consent_end_date` function when days argument is not provided."""
    end_date = consent_end_date()
    current_year = datetime.datetime.now().year
    expected_date = datetime.datetime(
        year=current_year,
        month=12,
        day=31,
        hour=23,
        minute=59,
        second=59,
        tzinfo=datetime.timezone.utc,
    )
    assert end_date == expected_date
