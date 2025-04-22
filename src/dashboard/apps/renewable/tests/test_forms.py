"""Dashboard renewable forms tests."""

import uuid

import pytest

from apps.consent.tests.conftest import patch_datetime_now  # noqa: F401
from apps.renewable.forms import RenewableReadingForm


@pytest.mark.django_db
def test_clean_collected_at(patch_datetime_now):  # noqa: F811
    """Test _clean_collected_at."""
    dp_id = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")

    # `meter_reading` is provided but not `collected_at`
    form = RenewableReadingForm(data={f"meter_reading_{dp_id}": 100})
    is_error = form._clean_collected_at(dp_id)
    assert is_error is True
    assert f"collected_at_{dp_id}" in form.field_errors
    assert (
        form.field_errors[f"collected_at_{dp_id}"]
        == "Collected date is required if a meter reading is provided"
    )

    # the `collected_at` date is in the future.
    future_date = "2999-01-01"
    form = RenewableReadingForm(data={f"collected_at_{dp_id}": future_date})
    is_error = form._clean_collected_at(dp_id)
    assert is_error is True
    assert f"collected_at_{dp_id}" in form.field_errors
    assert (
        form.field_errors[f"collected_at_{dp_id}"] == "The date cannot be in the future"
    )

    # `collected_at` is earlier than 10 days ago.
    early_date = "2000-01-01"
    form = RenewableReadingForm(data={f"collected_at_{dp_id}": early_date})
    is_error = form._clean_collected_at(dp_id)
    assert is_error is True
    assert f"collected_at_{dp_id}" in form.field_errors
    assert (
        form.field_errors[f"collected_at_{dp_id}"]
        == "The date cannot be earlier than 10 days"
    )

    # the `collected_at` date is valid.
    valid_date = "2025-01-03"
    form = RenewableReadingForm(
        data={
            f"collected_at_{dp_id}": valid_date,
            f"meter_reading_{dp_id}": 100,
        }
    )
    is_error = form._clean_collected_at(dp_id)
    assert is_error is False
    assert f"collected_at_{dp_id}" not in form.field_errors


@pytest.mark.django_db
def test_clean_meter_reading():
    """Test _clean_meter_reading."""
    dp_id = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")

    # don't fails if the value is missing
    form = RenewableReadingForm(data={})
    is_error = form._clean_meter_reading(dp_id)
    assert is_error is False

    # fails if the value is not a valid float number
    form = RenewableReadingForm(data={f"meter_reading_{dp_id}": "abc"})
    is_error = form._clean_meter_reading(dp_id)
    assert is_error is True
    assert f"meter_reading_{dp_id}" in form.field_errors
    assert form.field_errors[f"meter_reading_{dp_id}"] == "Invalid number format"

    # fails if the value is a negative number
    form = RenewableReadingForm(data={f"meter_reading_{dp_id}": "-10.5"})
    is_error = form._clean_meter_reading(dp_id)
    assert is_error is True
    assert f"meter_reading_{dp_id}" in form.field_errors
    assert form.field_errors[f"meter_reading_{dp_id}"] == "The value must be positive"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "meter_value",
    ["50.75", "50,75", "50", 50, 50.75, None, "", 0],
)
def test_clean_meter_reading_with_valid_data(meter_value):
    """Test _clean_meter_reading passes if the value is valid."""
    dp_id = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
    form = RenewableReadingForm(data={f"meter_reading_{dp_id}": meter_value})
    is_error = form._clean_meter_reading(dp_id)
    assert is_error is False
