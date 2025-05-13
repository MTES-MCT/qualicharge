"""Dashboard renewable_tags tests."""

from datetime import date
from unittest.mock import Mock

import pytest
from django.utils import timezone

from apps.renewable.templatetags.renewable_tags import (
    _get_reference_date,
    previous_quarter_period,
    previous_quarter_period_dates,
    quarter_period,
    quarter_period_dates,
    sort_formset_by_station,
)


def test_get_reference_date_with_valid_date(monkeypatch):
    """Test _get_reference_date."""
    # with a valid reference date
    reference_date = date(2025, 1, 1)
    result = _get_reference_date(reference_date)
    assert result == reference_date

    # when given a None value
    expected_date = date(2025, 5, 6)
    monkeypatch.setattr(timezone, "now", lambda: expected_date)
    result = _get_reference_date(None)
    assert result == expected_date


@pytest.mark.parametrize(
    "reference_date, expected_period",
    [
        (date(2025, 4, 1), "Q1 2025"),
        (date(2025, 1, 1), "Q4 2024"),
        (date(2025, 7, 15), "Q2 2025"),
    ],
)
def test_previous_quarter_period(reference_date, expected_period):
    """Test previous_quarter_period for various cases of reference_date."""
    result = previous_quarter_period(reference_date)
    assert result == expected_period


def test_previous_quarter_period_without_reference_date(monkeypatch):
    """Test previous_quarter_period without reference_date."""
    monkeypatch.setattr(timezone, "now", lambda: date(2025, 5, 6))
    result = previous_quarter_period()
    assert result == "Q1 2025"


@pytest.mark.parametrize(
    "reference_date, expected_period",
    [
        (date(2025, 4, 1), "Q2 2025"),
        (date(2025, 1, 1), "Q1 2025"),
        (date(2025, 7, 15), "Q3 2025"),
    ],
)
def test_quarter_period(reference_date, expected_period):
    """Test previous_quarter_period for various cases of reference_date."""
    result = quarter_period(reference_date)
    assert result == expected_period


def test_quarter_period_without_reference_date(monkeypatch):
    """Test previous_quarter_period without reference_date."""
    monkeypatch.setattr(timezone, "now", lambda: date(2025, 5, 6))
    result = quarter_period()
    assert result == "Q2 2025"


@pytest.mark.parametrize(
    "reference_date, expected_period",
    [
        (date(2025, 4, 1), "01/01/2025 to 31/03/2025"),
        (date(2025, 1, 1), "01/10/2024 to 31/12/2024"),
        (date(2025, 7, 15), "01/04/2025 to 30/06/2025"),
    ],
)
def test_previous_quarter_period_dates(reference_date, expected_period):
    """Test previous_quarter_period for various cases of reference_date."""
    result = previous_quarter_period_dates(reference_date)
    assert result == expected_period


def test_previous_quarter_period_dates_period_without_reference_date(monkeypatch):
    """Test previous_quarter_period without reference_date."""
    monkeypatch.setattr(timezone, "now", lambda: date(2025, 5, 6))
    result = previous_quarter_period_dates()
    assert result == "01/01/2025 to 31/03/2025"


@pytest.mark.parametrize(
    "reference_date, expected_period",
    [
        (date(2025, 4, 1), "01/04/2025 to 30/06/2025"),
        (date(2025, 1, 1), "01/01/2025 to 31/03/2025"),
        (date(2025, 7, 15), "01/07/2025 to 30/09/2025"),
    ],
)
def test_quarter_period_dates(reference_date, expected_period):
    """Test previous_quarter_period for various cases of reference_date."""
    result = quarter_period_dates(reference_date)
    assert result == expected_period


def test_quarter_period_dates_period_without_reference_date(monkeypatch):
    """Test previous_quarter_period without reference_date."""
    monkeypatch.setattr(timezone, "now", lambda: date(2025, 5, 6))
    result = quarter_period_dates()
    assert result == "01/04/2025 to 30/06/2025"


@pytest.mark.django_db
def test_sort_formset_by_station():
    """Test sort_formset_by_station."""
    # Test sort_formset_by_station with an empty formset
    formset = []
    result = sort_formset_by_station(formset)
    assert result == []

    # Test sort_formset_by_station with a populated formset
    # Mocking forms in the formset
    form1 = Mock()
    form1.instance = Mock()
    form1.instance.has_renewable = False
    form1.stations_grouped = {"Station C": None}

    form2 = Mock()
    form2.instance = Mock()
    form2.instance.has_renewable = True
    form2.stations_grouped = {"Station A": None}

    form3 = Mock()
    form3.instance = Mock()
    form3.instance.has_renewable = True
    form3.stations_grouped = {"Station B": None}

    formset = [form1, form2, form3]

    result = sort_formset_by_station(formset)

    # Expected order: form2 (Station A), form3 (Station B), form1 (Station C)
    assert result == [form2, form3, form1]
