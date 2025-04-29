"""Dashboard renewable forms tests."""

import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone

from apps.renewable.forms import RenewableReadingForm


def test_get_authorized_date_range(monkeypatch, settings):
    """Test _get_authorized_date_range()."""
    settings.RENEWABLE_MIN_DAYS_FOR_METER_READING = 15
    mock_now = date(2025, 3, 6)
    monkeypatch.setattr(timezone, "now", lambda: mock_now)

    min_date, end_date = RenewableReadingForm._get_authorized_date_range()

    # expected dates
    expected_min_date = date(2024, 12, 16)
    expected_end_date = date(2024, 12, 31)
    assert min_date == expected_min_date
    assert end_date == expected_end_date

    # check min_date is before end_date
    assert min_date < end_date

    # check the gap between min_date and end_date
    delta = end_date - min_date
    assert delta.days == settings.RENEWABLE_MIN_DAYS_FOR_METER_READING


@pytest.mark.parametrize(
    "test_date,expected_quarter_end",
    [
        (date(2025, 2, 15), date(2024, 12, 31)),
        (date(2025, 5, 15), date(2025, 3, 31)),
        (date(2025, 8, 15), date(2025, 6, 30)),
        (date(2025, 11, 15), date(2025, 9, 30)),
    ],
)
def test_get_authorized_date_range_different_quarters(
    test_date, expected_quarter_end, monkeypatch, settings
):
    """Test _get_authorized_date_range() with different quarters."""
    monkeypatch.setattr(timezone, "now", lambda: test_date)

    min_date, end_date = RenewableReadingForm._get_authorized_date_range()

    assert end_date == expected_quarter_end
    assert min_date == end_date - timedelta(
        days=settings.RENEWABLE_MIN_DAYS_FOR_METER_READING
    )


@pytest.mark.django_db
def test_clean_collected_at(monkeypatch):
    """Test _clean_collected_at."""
    mock_now = date(2025, 3, 6)
    monkeypatch.setattr(timezone, "now", lambda: mock_now)

    dp_id = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
    collected_at_key = f"collected_at_{dp_id}"
    meter_reading_key = f"meter_reading_{dp_id}"

    # `meter_reading` is provided but not `collected_at`
    form = RenewableReadingForm(data={meter_reading_key: 100})
    is_error = form._clean_collected_at(collected_at_key, meter_reading_key)
    assert is_error is True
    assert collected_at_key in form.field_errors
    assert (
        form.field_errors[collected_at_key]
        == "Collected date is required if a meter reading is provided"
    )

    # the `collected_at` date is in the future.
    future_date = "2999-01-01"
    form = RenewableReadingForm(data={collected_at_key: future_date})
    min_date, end_date = form._get_authorized_date_range()
    is_error = form._clean_collected_at(collected_at_key, meter_reading_key)
    assert is_error is True
    assert collected_at_key in form.field_errors
    assert (
        form.field_errors[collected_at_key] == "The date cannot be in the future. "
        f"Collected date should be between {min_date} and {end_date}."
    )

    # `collected_at` is earlier than 10 days ago.
    early_date = "2000-01-01"
    form = RenewableReadingForm(data={collected_at_key: early_date})
    min_date, end_date = form._get_authorized_date_range()
    is_error = form._clean_collected_at(collected_at_key, meter_reading_key)
    assert is_error is True
    assert collected_at_key in form.field_errors
    assert (
        form.field_errors[collected_at_key]
        == f"The date cannot be earlier than {min_date}. "
        f"Collected date should be between {min_date} and {end_date}."
    )

    # the `collected_at` date is valid.
    valid_date = "2024-12-18"
    form = RenewableReadingForm(
        data={
            collected_at_key: valid_date,
            meter_reading_key: 100,
        }
    )
    is_error = form._clean_collected_at(collected_at_key, meter_reading_key)
    assert is_error is False


@pytest.mark.django_db
def test_clean_meter_reading():
    """Test _clean_meter_reading."""
    dp_id = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
    meter_reading_key = f"meter_reading_{dp_id}"

    # don't fails if the value is missing
    form = RenewableReadingForm(data={})
    is_error = form._clean_meter_reading(meter_reading_key)
    assert is_error is False

    # fails if the value is not a valid float number
    form = RenewableReadingForm(data={meter_reading_key: "abc"})
    is_error = form._clean_meter_reading(meter_reading_key)
    assert is_error is True
    assert meter_reading_key in form.field_errors
    assert form.field_errors[meter_reading_key] == "Invalid number format"

    # fails if the value is a negative number
    form = RenewableReadingForm(data={meter_reading_key: "-10.5"})
    is_error = form._clean_meter_reading(meter_reading_key)
    assert is_error is True
    assert meter_reading_key in form.field_errors
    assert form.field_errors[meter_reading_key] == "The value must be positive"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "meter_value",
    ["50.75", "50,75", "50", 50, 50.75, None, "", 0],
)
def test_clean_meter_reading_with_valid_data(meter_value):
    """Test _clean_meter_reading passes if the value is valid."""
    dp_id = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
    meter_reading_key = f"meter_reading_{dp_id}"

    form = RenewableReadingForm(data={meter_reading_key: meter_value})
    is_error = form._clean_meter_reading(meter_reading_key)
    assert is_error is False
