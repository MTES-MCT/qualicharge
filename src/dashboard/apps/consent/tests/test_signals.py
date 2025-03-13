"""Dashboard consent signals tests."""

import pytest

from apps.consent import AWAITING
from apps.consent.utils import consent_end_date


@pytest.mark.django_db
def test_handle_new_delivery_point(patch_datetime_now):
    """Tests the signal after a new DeliveryPoint is saved."""
    from apps.consent.models import Consent
    from apps.core.factories import DeliveryPointFactory

    assert Consent.objects.count() == 0

    delivery_point = DeliveryPointFactory()

    assert Consent.objects.count() == 1

    consent = Consent.objects.first()
    assert consent.delivery_point == delivery_point
    assert consent.created_by == delivery_point.entity.users.first()
    assert consent.status == AWAITING
    assert consent.revoked_at is None
    assert consent.start is not None
    assert consent.end is not None

    expected_end_date = consent_end_date()
    assert consent.end.year == expected_end_date.year
    assert consent.end.month == expected_end_date.month
    assert consent.end.day == expected_end_date.day

    assert consent.id_station_itinerance is not None
    assert consent.station_name is not None
    assert consent.provider_assigned_id is not None

    assert consent.id_station_itinerance == delivery_point.id_station_itinerance
    assert consent.station_name == delivery_point.station_name
    assert consent.provider_assigned_id == delivery_point.provider_assigned_id
