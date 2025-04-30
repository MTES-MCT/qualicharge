"""Dashboard renewable app template tags."""

from datetime import date

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from apps.core.utils import get_previous_quarter_date_range, get_quarter_number

register = template.Library()


@register.simple_tag
def quarter_period():
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

    suffix = {
        1: _("st"),
        2: _("nd"),
        3: _("rd"),
        4: _("th"),
    }[quarter]

    return mark_safe(  # noqa: S308
        _(
            f"{quarter}{suffix} quarter {start_date.strftime('%Y')}  <br />"
            f"{start_date.strftime('%d/%m/%Y')} to {last_date.strftime('%d/%m/%Y')}"
        )
    )
