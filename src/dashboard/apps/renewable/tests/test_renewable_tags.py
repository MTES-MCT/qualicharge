"""Dashboard renewable_tags tests."""

from datetime import date
from unittest.mock import patch

import pytest
from django.utils.safestring import SafeString

from apps.renewable.templatetags.renewable_tags import quarter_period

QUARTER_TEST_CASES = [
    {
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 3, 31),
        "quarter": 1,
        "expected": "1st quarter 2025  <br />01/01/2025 to 31/03/2025",
    },
    {
        "start_date": date(2025, 4, 1),
        "end_date": date(2025, 6, 30),
        "quarter": 2,
        "expected": "2nd quarter 2025  <br />01/04/2025 to 30/06/2025",
    },
    {
        "start_date": date(2025, 7, 1),
        "end_date": date(2025, 9, 30),
        "quarter": 3,
        "expected": "3rd quarter 2025  <br />01/07/2025 to 30/09/2025",
    },
    {
        "start_date": date(2025, 10, 1),
        "end_date": date(2025, 12, 31),
        "quarter": 4,
        "expected": "4th quarter 2025  <br />01/10/2025 to 31/12/2025",
    },
]


@pytest.mark.django_db
@pytest.mark.parametrize("test_case", QUARTER_TEST_CASES)
@patch("apps.renewable.templatetags.renewable_tags.get_quarter_number")
@patch("apps.renewable.templatetags.renewable_tags.get_previous_quarter_date_range")
def test_quarter_period_returns_safe_string(
    mock_get_previous_quarter_date_range, mock_get_quarter_number, test_case
):
    """Test quarter_period returns SafeString."""
    mock_get_previous_quarter_date_range.return_value = (
        test_case["start_date"],
        test_case["end_date"],
    )
    mock_get_quarter_number.return_value = test_case["quarter"]

    result = quarter_period()

    assert isinstance(result, SafeString)
    assert test_case["expected"] in result
