"""Dashboard renewable app template tags."""

from datetime import date, datetime
from typing import Any

from django import template
from django.db.models import QuerySet
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext as _

from apps.core.utils import (
    get_previous_quarter_date_range,
    get_quarter_date_range,
    get_quarter_number,
)

register = template.Library()

SUFFIXES = {
    1: _("st"),
    2: _("nd"),
    3: _("rd"),
    4: _("th"),
}


@register.filter
def sort_submitted_renewable_by_station(renewables: QuerySet) -> list[Any]:
    """Sorts a queryset of renewables by their associated delivery points station names.

    This function returns a sorted list of dictionaries with this structured
    data, ordered by `collected_at` date and by the first station name in a
    case-insensitive manner.

    Args:
        renewables (QuerySet): A queryset of renewablesobjects.

    Returns:
        list[Any]: A sorted list of dictionaries, each containing structured data about
            the delivery point and its related stations.

    """
    structured_renewables = [
        {
            **renewable.__dict__,
            "provider_assigned_id": renewable.delivery_point.provider_assigned_id,
            "stations_grouped": renewable.delivery_point.get_linked_stations(),
        }
        for renewable in renewables
    ]

    return sorted(
        structured_renewables,
        key=lambda x: (
            -x["collected_at"].timestamp(),
            (
                list(x["stations_grouped"].keys())[0].casefold()
                if x["stations_grouped"]
                else ""
            ),
        ),
    )


@register.simple_tag
def display_renewable_reading_period() -> SafeString:
    """Return the quarter period for renewable energy readings as a safe-escaped string.

    In the context of renewable meter readings, this returns the previous quarter
    relative to the current quarter.
    For example:
    - When in Q2 2024, returns Q1 2024
    - When in Q3 2024, returns Q2 2024

    Returns:
        SafeString: A safe-escaped string representing the quarter period, including
        the quarter number with its suffix and the date range of the quarter,
        formatted for display.
    """
    reference_date = date.today()

    start_date, last_date = get_previous_quarter_date_range(reference_date)
    quarter = get_quarter_number(start_date)

    return format_quarter_display_string(start_date, last_date, quarter)


@register.simple_tag
def display_quarter_period(reference_date: datetime) -> SafeString:
    """Return the quarter period for a given date as a safe-escaped string.

    In the context of renewable meter readings, this returns the previous quarter
    relative to the current quarter.
    For example:
    - 01/06/2024, returns Q2 2024
    - 01/01/2024, returns Q1 2024

    Returns:
        SafeString: A safe-escaped string representing the quarter period, including
        the quarter number with its suffix and the date range of the quarter,
        formatted for display.
    """
    start_date, last_date = get_quarter_date_range(reference_date)
    quarter = get_quarter_number(start_date)

    return format_quarter_display_string(start_date, last_date, quarter)


def format_quarter_display_string(
    start_date: date, last_date: date, quarter: int
) -> SafeString:
    """Return the quarter information as a safe-escaped string."""
    return mark_safe(  # noqa: S308
        _(
            f"{quarter}{SUFFIXES[quarter]} quarter {start_date.strftime('%Y')}  <br />"
            f"{start_date.strftime('%d/%m/%Y')} to {last_date.strftime('%d/%m/%Y')}"
        )
    )
