"""Dashboard consent app utils."""

import datetime
from typing import Any

from django.db.models import QuerySet

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


def order_consents_by_station(consents: QuerySet) -> list[Any]:
    """Orders consents by station name.

    This function processes a given QuerySet of consents, structures the data by
    adding delivery points and grouping stations linked with each delivery point.
    The consents are then sorted based on the case-insensitive name of the first
    station in the grouped stations list.

    Parameters:
        consents (QuerySet): A QuerySet of consent objects.

    Returns:
        list[Any]: A list of structured consents, sorted by station names.
            Each structured consent is a dictionary containing the original consent
            attributes, the associated delivery_point, and the grouped stations.
    """
    structured_consents = [
        {
            **consent.__dict__,
            "delivery_point": consent.delivery_point,
            "stations_grouped": consent.delivery_point.get_linked_stations(),
        }
        for consent in consents
    ]

    sorted_consents = sorted(
        structured_consents,
        key=lambda x: (
            list(x["stations_grouped"].keys())[0].casefold()
            if x["stations_grouped"]
            else ""
        ),
    )

    return sorted_consents
