"""Dashboard consent models tests."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db.models import signals

from apps.consent import AWAITING, REVOKED, VALIDATED
from apps.consent.factories import ConsentFactory
from apps.consent.signals import handle_new_delivery_point
from apps.consent.utils import consent_end_date
from apps.core.factories import DeliveryPointFactory
from apps.core.models import DeliveryPoint


@pytest.mark.django_db
def test_create_consent(patch_datetime_now):
    """Tests the creation of a consent."""
    from apps.consent.factories import ConsentFactory
    from apps.consent.models import Consent

    assert Consent.objects.count() == 0

    # create one `consent`
    signals.post_save.disconnect(
        receiver=handle_new_delivery_point,
        sender=DeliveryPoint,
        dispatch_uid="handle_new_delivery_point",
    )

    delivery_point = DeliveryPointFactory()
    consent = ConsentFactory(
        delivery_point=delivery_point, created_by=delivery_point.entity.users.first()
    )

    signals.post_save.connect(
        receiver=handle_new_delivery_point,
        sender=DeliveryPoint,
        dispatch_uid="handle_new_delivery_point",
    )

    assert Consent.objects.count() == 1

    assert consent.delivery_point == delivery_point
    assert consent.created_by == delivery_point.entity.users.first()
    assert consent.status == AWAITING
    assert consent.revoked_at is None
    assert consent.start is not None
    assert consent.end is not None

    # test consent.end is the last day of the year
    expected_end_date = consent_end_date()
    assert consent.end == expected_end_date

    # test created_at and updated_at have been updated.
    assert consent.created_at is not None
    assert consent.updated_at is not None


@pytest.mark.django_db
def test_create_consent_with_custom_period_date():
    """Tests the creation of a consent with a custom period date (`start` / `end`)."""
    from apps.consent.factories import ConsentFactory
    from apps.consent.models import Consent

    expected_start_date = datetime.datetime(
        year=2024,
        month=12,
        day=20,
        hour=17,
        minute=5,
        second=2,
        tzinfo=datetime.timezone.utc,
    )
    expected_end_date = expected_start_date + datetime.timedelta(days=2)

    # Create one consent with custom start / end date
    # we have to disconnect the signals that allow the creation of a consent after the
    # creation of a delivery point:
    # `ConsentFactory` creates a new `delivery_point` which itself creates a new
    # `consent`.
    assert Consent.objects.count() == 0
    signals.post_save.disconnect(
        receiver=handle_new_delivery_point,
        sender=DeliveryPoint,
        dispatch_uid="handle_new_delivery_point",
    )

    consent = ConsentFactory(start=expected_start_date, end=expected_end_date)

    signals.post_save.connect(
        receiver=handle_new_delivery_point,
        sender=DeliveryPoint,
        dispatch_uid="handle_new_delivery_point",
    )
    assert Consent.objects.count() == 1

    assert consent.start == expected_start_date
    assert consent.end == expected_end_date


@pytest.mark.django_db
def test_update_consent_status():
    """Tests updating a consent status.

    Test that consents can no longer be modified once their status is passed to
    `VALIDATED` (raise ValidationError).
    """
    from apps.consent.models import Consent

    # create one `delivery_point` and consequently one `consent`
    assert Consent.objects.count() == 0
    delivery_point = DeliveryPointFactory()
    assert Consent.objects.count() == 1

    # get the created consent
    consent = Consent.objects.get(delivery_point=delivery_point)
    consent_updated_at = consent.updated_at
    assert consent.status == AWAITING
    assert consent.revoked_at is None

    # update status to REVOKED
    consent.status = REVOKED
    consent.save()
    assert consent.status == REVOKED
    assert consent.updated_at > consent_updated_at
    assert consent.revoked_at is not None
    new_updated_at = consent.updated_at
    # refresh the state in memory
    consent = Consent.objects.get(delivery_point=delivery_point)

    # Update the consent to AWAITING
    consent.status = AWAITING
    consent.revoked_at = None
    consent.save()
    assert consent.status == AWAITING
    assert consent.updated_at > new_updated_at
    assert consent.revoked_at is None
    new_updated_at = consent.updated_at
    # refresh the state in memory
    consent = Consent.objects.get(delivery_point=delivery_point)

    # update status to VALIDATED
    consent.status = VALIDATED
    consent.revoked_at = None
    consent.save()
    assert consent.status == VALIDATED
    assert consent.updated_at > new_updated_at
    assert consent.revoked_at is None
    # refresh the state in memory
    consent = Consent.objects.get(delivery_point=delivery_point)

    # The consent status is `VALIDATED`, so it cannot be changed anymore.
    with pytest.raises(ValidationError):
        consent.status = AWAITING
        consent.save()


@pytest.mark.django_db
def test_delete_consent():
    """Tests deleting a consent.

    Consents can no longer be deleted once their status is passed to
    `VALIDATED` (raise ValidationError).
    """
    from apps.consent.models import Consent

    # create one `delivery_point` and consequently one `consent`
    assert Consent.objects.count() == 0
    delivery_point = DeliveryPointFactory()
    assert Consent.objects.count() == 1

    # get the created consent and delete it
    consent = Consent.objects.get(delivery_point=delivery_point)
    assert consent.status != VALIDATED
    consent.delete()
    assert Consent.objects.count() == 0

    # create a new content with status VALIDATED
    ConsentFactory(delivery_point=delivery_point, status=VALIDATED)
    consent = Consent.objects.get(delivery_point=delivery_point)
    assert consent.status == VALIDATED
    # the consent status is `VALIDATED`, so it cannot be deleted.
    with pytest.raises(ValidationError):
        consent.delete()
    assert Consent.objects.count() == 1
