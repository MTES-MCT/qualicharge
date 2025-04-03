"""Dashboard consent app utils."""

import datetime

from .settings import CONSENT_NUMBER_DAYS_END_DATE


def consent_start_date() -> datetime.datetime:
    """Calculate the start date of the consent period."""
    current_year = datetime.datetime.now().year
    return datetime.datetime(
        year=current_year, month=1, day=1, tzinfo=datetime.timezone.utc
    )


def consent_end_date(
    days: int | None = CONSENT_NUMBER_DAYS_END_DATE,
) -> datetime.datetime:
    """Calculate the end date of the consent period.

    Returns a specific end date based on the number of days provided,
    or the default end of the year date if no argument is passed.

    Parameters:
        days (int | None): An optional number of days to calculate the future date.
                    If None, the function defaults to the end of the current year.
    """
    if days:
        return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=days
        )

    return datetime.datetime.now(datetime.timezone.utc).replace(
        month=12, day=31, hour=23, minute=59, second=59, microsecond=0
    )
