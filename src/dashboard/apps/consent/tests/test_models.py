"""Dashboard consent models tests."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import formats, timezone

from apps.consent.models import Consent
from apps.core.models import DeliveryPoint


@pytest.mark.django_db
def test_create_consent():
    """Tests the creation of a consent."""
    # create user
    User = get_user_model()
    user1 = User.objects.create_user(username="user1", password="foo")  # noqa: S106

    # create delivery point
    delivery_point = DeliveryPoint.objects.create(provider_id="provider_1234")

    # create consent
    consent = Consent.objects.create(
        delivery_point=delivery_point,
        created_by=user1,
        start=timezone.now(),
        end=timezone.now() + timedelta(days=90),
    )
    assert consent.delivery_point == delivery_point
    assert consent.created_by == user1
    assert consent.status == Consent.AWAITING
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
    # create user
    User = get_user_model()
    user1 = User.objects.create_user(username="user1", password="foo")  # noqa: S106

    # create delivery point
    delivery_point = DeliveryPoint.objects.create(provider_id="provider_1234")

    # create consent
    consent = Consent.objects.create(
        delivery_point=delivery_point,
        created_by=user1,
        start=timezone.now(),
        end=timezone.now() + timedelta(days=90),
    )
    new_updated_at = consent.updated_at

    # update status to VALIDATED
    consent.status = Consent.VALIDATED
    consent.save()
    assert consent.status == Consent.VALIDATED
    assert consent.updated_at > new_updated_at
    assert consent.revoked_at is None
    new_updated_at = consent.updated_at

    # update status to REVOKED
    consent.status = Consent.REVOKED
    consent.save()
    assert consent.status == Consent.REVOKED
    assert consent.updated_at > new_updated_at
    assert consent.revoked_at is not None
