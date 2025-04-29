"""Dashboard core utils tests."""

from datetime import date

import pytest
from django.utils import timezone as django_timezone

from apps.core.utils import (
    get_current_quarter_date_range,
    get_previous_quarter_date_range,
    get_quarter_date_range,
)

QUARTER_TEST_CASES = [
    (
        date(2025, 1, 6),  # testing date
        date(2025, 1, 1),  # expected start date
        date(2025, 3, 31),  # expected end dat
    ),
    (date(2025, 3, 6), date(2025, 1, 1), date(2025, 3, 31)),
    (date(2025, 5, 6), date(2025, 4, 1), date(2025, 6, 30)),
    (date(2025, 12, 6), date(2025, 10, 1), date(2025, 12, 31)),
]

PREVIOUS_QUARTER_TEST_CASES = [
    (
        date(2025, 1, 6),  # testing date
        date(2024, 10, 1),  # expected start date
        date(2024, 12, 31),  # expected end dat
    ),
    (date(2025, 3, 6), date(2024, 10, 1), date(2024, 12, 31)),
    (date(2025, 5, 6), date(2025, 1, 1), date(2025, 3, 31)),
    (date(2025, 12, 6), date(2025, 7, 1), date(2025, 9, 30)),
]


@pytest.mark.parametrize("test_date,expected_start,expected_end", QUARTER_TEST_CASES)
def test_get_quarter_date_range_start_and_end_dates(
    monkeypatch, test_date, expected_start, expected_end
):
    """Test if range dates of the quarter are calculated correctly."""
    start_date, end_date = get_quarter_date_range(test_date)
    assert start_date == expected_start
    assert end_date == expected_end


@pytest.mark.parametrize("test_date,expected_start,expected_end", QUARTER_TEST_CASES)
def test_get_current_quarter_date_range_start_and_end_dates(
    monkeypatch, test_date, expected_start, expected_end
):
    """Test if range dates of the quarter are calculated correctly."""
    # test without date parameter
    monkeypatch.setattr(django_timezone, "now", lambda: test_date)
    start_date, end_date = get_current_quarter_date_range()
    assert start_date == expected_start
    assert end_date == expected_end


@pytest.mark.parametrize(
    "test_date,expected_start,expected_end", PREVIOUS_QUARTER_TEST_CASES
)
def test_get_previous_quarter_date_range_start_and_end_dates(
    monkeypatch, test_date, expected_start, expected_end
):
    """Test if previous range dates of the previous quarter are calculated correctly."""
    # test with date parameter
    start_date, end_date = get_previous_quarter_date_range(test_date)
    assert start_date == expected_start
    assert end_date == expected_end
