"""Dashboard core utils."""

import datetime

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from apps.core.validators import validate_siret


def siret2siren(siret: str) -> str:
    """Convert a SIRET to a SIREN."""
    validate_siret(siret)
    return siret[:9]


def get_current_quarter_date_range() -> tuple[datetime.date, datetime.date]:
    """Get the start and end day of the current quarter."""
    now: datetime.date = timezone.now()

    current_quarter = (now.month - 1) // 3
    first_day: datetime.date = datetime.datetime(now.year, current_quarter * 3 + 1, 1)
    last_day: datetime.date = first_day + relativedelta(months=3, days=-1)

    return first_day, last_day
