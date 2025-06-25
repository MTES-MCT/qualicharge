"""Dashboard core app template tags."""

from typing import Any

from django import template
from django.db.models import QuerySet

register = template.Library()


@register.filter
def sort_by_station(delivery_points: QuerySet) -> list[Any]:
    """Sorts a queryset of delivery points by their associated station names.

    This function returns a sorted list of dictionaries with this structured
    data, ordered by the first station name in a case-insensitive manner.

    Args:
        delivery_points (QuerySet): A queryset of delivery points objects.

    Returns:
        list[Any]: A sorted list of dictionaries, each containing structured data about
            the delivery point and its related stations.
    """
    structured_delivery_points = [
        {
            **dp.__dict__,
            "stations_grouped": dp.get_linked_stations(),
        }
        for dp in delivery_points
    ]

    return sorted(
        structured_delivery_points,
        key=lambda x: (
            list(x["stations_grouped"].keys())[0].casefold()
            if x["stations_grouped"]
            else ""
        ),
    )
