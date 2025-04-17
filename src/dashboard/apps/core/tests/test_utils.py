"""Dashboard core utils tests."""

from datetime import datetime

import pytest
from django.utils import timezone as django_timezone

from apps.core.utils import get_current_quarter_date_range

QUARTER_TEST_CASES = [
    (
        datetime(2025, 1, 6),  # testing date
        datetime(2025, 1, 1),  # expected start date
        datetime(2025, 3, 31),  # expected end date
    ),
    (datetime(2025, 3, 6), datetime(2025, 1, 1), datetime(2025, 3, 31)),
    (datetime(2025, 5, 6), datetime(2025, 4, 1), datetime(2025, 6, 30)),
    (datetime(2025, 12, 6), datetime(2025, 10, 1), datetime(2025, 12, 31)),
]


@pytest.mark.parametrize("test_date,expected_start,expected_end", QUARTER_TEST_CASES)
def test_get_current_quarter_date_range_start_and_end_dates(
    monkeypatch, test_date, expected_start, expected_end
):
    """Test if the start and end dates of the quarter are calculated correctly."""
    monkeypatch.setattr(django_timezone, "now", lambda: test_date)

    start_date, end_date = get_current_quarter_date_range()

    assert start_date == expected_start
    assert end_date == expected_end
