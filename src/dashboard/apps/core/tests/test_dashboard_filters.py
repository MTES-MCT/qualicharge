"""Dashboard core mixins tests."""

import pytest

from apps.core.factories import DeliveryPointFactory, EntityFactory, StationFactory
from apps.core.models import DeliveryPoint
from apps.core.templatetags.dashboard_filters import sort_by_station


@pytest.mark.django_db
def test_sort_by_station():
    """Test `order_consents_by_station` function."""
    # test order_consents_by_station() without station
    assert DeliveryPoint.objects.all().count() == 0
    delivery_points = DeliveryPoint.objects.all()
    results = sort_by_station(delivery_points)
    assert results == []

    # create entity, delivery points, consents and stations
    entity1 = EntityFactory()
    dp_1 = DeliveryPointFactory(entity=entity1)
    dp_2 = DeliveryPointFactory(entity=entity1)
    dp_3 = DeliveryPointFactory(entity=entity1)

    # stations are created in a non-alphabetical order
    StationFactory(
        delivery_point=dp_1, station_name="B", id_station_itinerance="FRABCP01"
    )
    StationFactory(
        delivery_point=dp_2, station_name="C", id_station_itinerance="FRDEFP05"
    )
    StationFactory(
        delivery_point=dp_2, station_name="y", id_station_itinerance="FRDEFP02"
    )
    StationFactory(
        delivery_point=dp_2, station_name="A", id_station_itinerance="FRDEFP03"
    )
    StationFactory(
        delivery_point=dp_2, station_name="p", id_station_itinerance="FRDEFP04"
    )
    StationFactory(
        delivery_point=dp_3, station_name="d", id_station_itinerance="FRGHIP01"
    )

    delivery_points = DeliveryPoint.objects.all()
    results = sort_by_station(delivery_points)

    for result in results:
        # test retrieving the “standard” information from a consent
        assert result["id"] in [dp_1.id, dp_2.id, dp_3.id]
        assert result["provider_assigned_id"] is not None

    # Extract station names from grouped stations for comparison
    ordered_station_names = [
        list(result["stations_grouped"].keys())[0] for result in results
    ]
    assert ordered_station_names == sorted(ordered_station_names, key=str.casefold)
