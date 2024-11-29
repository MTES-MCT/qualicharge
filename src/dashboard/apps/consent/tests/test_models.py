"""Dashboard consent models tests."""

from datetime import timedelta

import pytest
from django.utils import formats

from apps.auth.factories import UserFactory
from apps.consent import AWAITING, REVOKED, VALIDATED
from apps.consent.factories import ConsentFactory
from apps.core.factories import DeliveryPointFactory


@pytest.mark.django_db
def test_create_consent():
    """Tests the creation of a consent."""
    user1 = UserFactory()
    delivery_point = DeliveryPointFactory()

    consent = ConsentFactory(
        delivery_point=delivery_point,
        created_by=user1,
    )

    assert consent.delivery_point == delivery_point
    assert consent.created_by == user1
    assert consent.status == AWAITING
    assert consent.revoked_at is None
    assert consent.start is not None
    assert consent.end is not None

    # test consent.end is 90 days later than the consent.start
    end_date = consent.start + timedelta(days=90)
    consent_start = formats.date_format(end_date, "Y/m/d")
    consent_end = formats.date_format(consent.end, "Y/m/d")
    assert consent_start == consent_end

    # test created_at and updated_at have been updated.
    assert consent.created_at is not None
    assert consent.updated_at is not None


@pytest.mark.django_db
def test_update_consent_status():
    """Tests updating a consent status."""
    user1 = UserFactory()
    delivery_point = DeliveryPointFactory()

    consent = ConsentFactory(
        delivery_point=delivery_point,
        created_by=user1,
    )

    new_updated_at = consent.updated_at

    # update status to VALIDATED
    consent.status = VALIDATED
    consent.save()
    assert consent.status == VALIDATED
    assert consent.updated_at > new_updated_at
    assert consent.revoked_at is None
    new_updated_at = consent.updated_at

    # update status to REVOKED
    consent.status = REVOKED
    consent.save()
    assert consent.status == REVOKED
    assert consent.updated_at > new_updated_at
    assert consent.revoked_at is not None
