"""Dashboard core utils."""

from datetime import date
from typing import Tuple

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from apps.core.validators import validate_siret

DateRange = Tuple[date, date]
MONTHS_PER_QUARTER = 3


def siret2siren(siret: str) -> str:
    """Convert a SIRET to a SIREN."""
    validate_siret(siret)
    return siret[:9]


def get_quarter_date_range(reference_date: date) -> DateRange:
    """Get the start and end day of a quarter for a given date."""
    current_quarter = (reference_date.month - 1) // MONTHS_PER_QUARTER
    first_day: date = date(reference_date.year, current_quarter * 3 + 1, 1)
    last_day: date = first_day + relativedelta(months=MONTHS_PER_QUARTER, days=-1)

    return first_day, last_day


def get_current_quarter_date_range() -> DateRange:
    """Get the start and end day of the current quarter."""
    return get_quarter_date_range(timezone.now())


def get_previous_quarter_date_range(reference_date: date) -> DateRange:
    """Get the start and end day of the previous quarter of a given date."""
    return get_quarter_date_range(reference_date - relativedelta(months=3))


def get_quarter_number(reference_date: date) -> int:
    """Determines the quarter number for a given date.

    Args:
        reference_date: The date for which to calculate the quarter.
              If None, uses the current date.

    Returns:
        int: The quarter number (1-4).
              Q1: January-March
              Q2: April-June
              Q3: July-September
              Q4: October-December
    """
    first_day, _ = get_quarter_date_range(reference_date)
    return (first_day.month - 1) // MONTHS_PER_QUARTER + 1
