"""Dashboard consent app template tags."""

from typing import Any

from django import template
from django.db.models import QuerySet

register = template.Library()


@register.filter
def sort_by_station(consents: QuerySet) -> list[Any]:
    """Sorts a queryset of consents by their associated station names.

    This function returns a sorted list of dictionaries with this structured
    data, ordered by the first station name in a case-insensitive manner.

    Args:
        consents (QuerySet): A queryset of consent objects.

    Returns:
        list[Any]: A sorted list of dictionaries, each containing structured data about
            the consent and its related stations.

    """
    structured_consents = [
        {
            **consent.__dict__,
            "provider_assigned_id": consent.delivery_point.provider_assigned_id,
            "stations_grouped": consent.delivery_point.get_linked_stations(),
        }
        for consent in consents
    ]

    return sorted(
        structured_consents,
        key=lambda x: (
            list(x["stations_grouped"].keys())[0].casefold()
            if x["stations_grouped"]
            else ""
        ),
    )
