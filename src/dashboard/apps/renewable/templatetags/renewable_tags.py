"""Dashboard renewable app template tags."""

from datetime import date

from django import template
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core.utils import (
    get_previous_quarter_date_range,
    get_quarter_date_range,
    get_quarter_number,
)

register = template.Library()


def _get_reference_date(reference_date: date | None) -> date:
    """Return the reference date or today if None."""
    return reference_date or timezone.now()


def _format_quarter_period(start_date: date) -> str:
    """Format quarter period string."""
    quarter = get_quarter_number(start_date)
    return _("Q%(quarter)s %(year)s") % {
        "quarter": quarter,
        "year": start_date.strftime("%Y"),
    }


def _format_date_range(start_date: date, end_date: date) -> str:
    """Format date range string."""
    return _("%(start_date)s to %(end_date)s") % {
        "start_date": start_date.strftime("%d/%m/%Y"),
        "end_date": end_date.strftime("%d/%m/%Y"),
    }


@register.simple_tag
def previous_quarter_period(reference_date: date | None = None) -> str:
    """Return formatted string for previous quarter period.

    For example, when reference_date is in Q2 2024, returns Q1 2024.
    """
    start_date, _ = get_previous_quarter_date_range(_get_reference_date(reference_date))
    return f"{_format_quarter_period(start_date)}"


@register.simple_tag
def quarter_period(reference_date: date | None = None) -> str:
    """Return formatted string for current quarter period."""
    start_date, _ = get_quarter_date_range(_get_reference_date(reference_date))
    return f"{_format_quarter_period(start_date)}"


@register.simple_tag
def previous_quarter_period_dates(reference_date: date | None = None):
    """Return formatted date range string for previous quarter."""
    start_date, end_date = get_previous_quarter_date_range(
        _get_reference_date(reference_date)
    )
    return _format_date_range(start_date, end_date)


@register.simple_tag
def quarter_period_dates(reference_date: date | None = None):
    """Return formatted date range string for current quarter."""
    start_date, end_date = get_quarter_date_range(_get_reference_date(reference_date))
    return _(_format_date_range(start_date, end_date))
