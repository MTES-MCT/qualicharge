"""Dashboard consent models tests."""

import datetime

import pytest
from django.db.models import signals

from apps.consent import AWAITING, REVOKED, VALIDATED
from apps.consent.exceptions import ConsentWorkflowError
from apps.consent.factories import ConsentFactory
from apps.consent.signals import handle_new_delivery_point
from apps.consent.tests.conftest import FAKE_TIME
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
def test_is_update_allowed():
    """Tests the `_is_update_allowed` method of a consent.

    - AWAITING to VALIDATED is allowed.
    - AWAITING to REVOKED is allowed.
    - VALIDATED to AWAITING is not allowed.
    - VALIDATED to REVOKED with not-allowed fields is not allowed.
    - VALIDATED to REVOKED with allowed fields is allowed.
    - REVOKED to AWAITING is allowed.
    - REVOKED to VALIDATED is allowed.
    - Create new consent is allowed.
    """
    from apps.consent.models import Consent

    # update from AWAITING to VALIDATED
    consent = ConsentFactory(status=AWAITING)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = VALIDATED
    assert consent._is_update_allowed() is True

    # update from AWAITING to REVOKED
    consent = ConsentFactory(status=AWAITING)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = REVOKED
    assert consent._is_update_allowed() is True

    # update from VALIDATED to AWAITING, raise exception
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = AWAITING
    with pytest.raises(
        ConsentWorkflowError,
        match='Validated consent can only be changed to the status "revoked".',
    ):
        consent._is_update_allowed()

    # update from VALIDATED to REVOKED
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = REVOKED
    assert consent._is_update_allowed() is True

    # update from VALIDATED to REVOKED with not-allowed fields raise exception
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = REVOKED
    consent.end = FAKE_TIME
    with pytest.raises(
        ConsentWorkflowError,
        match="['Only the authorized fields (revoked_at, status, updated_at) can be "
        "modified.']",
    ):
        consent._is_update_allowed()

    # update from VALIDATED to REVOKED with allowed fields.
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = REVOKED
    consent.revoked_at = consent.revoked_at or consent.start
    assert consent._is_update_allowed() is True

    # update from REVOKED to AWAITING
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = AWAITING
    assert consent._is_update_allowed() is True

    # update from REVOKED to VALIDATED
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = VALIDATED
    assert consent._is_update_allowed() is True

    # create a new consent
    dl = DeliveryPointFactory()
    consent = Consent(delivery_point=dl, status=AWAITING)
    assert consent._state.adding is True
    assert consent._is_update_allowed() is True


@pytest.mark.django_db
def test_clean_and_update_awaiting_consent_status():
    """Tests clean and update an awaiting consent status.

    - AWAITING to VALIDATED is authorized.
    - AWAITING to REVOKED is authorized.
    - AWAITING with mixed fields is authorized.
    """
    from apps.consent.models import Consent

    # update the status from AWAITING to VALIDATED
    consent = ConsentFactory(status=AWAITING)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = VALIDATED
    consent.end = FAKE_TIME
    consent.clean()
    consent.save()
    assert consent.status == VALIDATED
    assert consent.end == FAKE_TIME

    # update the status from AWAITING to REVOKED
    consent = ConsentFactory(status=AWAITING)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = REVOKED
    consent.end = FAKE_TIME
    consent.clean()
    consent.save()
    assert consent.status == REVOKED
    assert consent.end == FAKE_TIME
    assert consent.revoked_at is not None

    # update values
    consent = ConsentFactory(status=AWAITING)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.end = FAKE_TIME
    consent.clean()
    consent.save()
    assert consent.end == FAKE_TIME


@pytest.mark.django_db
def test_update_validated_consent_status():
    """Tests updating a validated consent status.

    - VALIDATED to AWAITING is not authorized.
    - VALIDATED to REVOKED with allowed fields is authorized.
    - VALIDATED to REVOKED with not-allowed fields is not authorized.
    - VALIDATED with mixed fields is not authorized.
    """
    from apps.consent.models import Consent

    # update the status from VALIDATED to AWAITING raise exception
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = AWAITING
    with pytest.raises(
        ConsentWorkflowError,
        match='Validated consent can only be changed to the status "revoked".',
    ):
        consent.save()

    # update the status from VALIDATED to REVOKED with allowed fields is authorized.
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = REVOKED
    consent.revoked_at = FAKE_TIME
    consent.save()
    assert consent.status == REVOKED
    assert consent.revoked_at is not None

    # update status VALIDATED to REVOKED with not-allowed field raise exception
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = REVOKED
    # update of an unauthorized field
    consent.end = FAKE_TIME
    with pytest.raises(
        ConsentWorkflowError,
        match="['Only the authorized fields (revoked_at, status, updated_at) can be "
        "modified.']",
    ):
        consent.save()

    # update status with mixed fields raise exception
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    # update of an unauthorized field
    consent.end = FAKE_TIME
    with pytest.raises(
        ConsentWorkflowError,
        match='Validated consent can only be changed to the status "revoked".',
    ):
        consent.save()


@pytest.mark.django_db
def test_update_revoked_consent_status():
    """Tests updating a revoked consent status.

    - REVOKED to AWAITING is authorized.
    - REVOKED to VALIDATED is authorized.
    - REVOKED with mixed fields is authorized.
    """
    from apps.consent.models import Consent

    # update the status from REVOKED to AWAITING
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = AWAITING
    consent.save()
    assert consent.status == AWAITING

    # update the status from REVOKED to VALIDATED
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = VALIDATED
    consent.save()
    assert consent.status == VALIDATED

    # update status with mixed fields
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.end = FAKE_TIME
    consent.save()
    assert consent.status == REVOKED
    assert consent.end == FAKE_TIME


@pytest.mark.django_db
def test_clean_validated_consent_status():
    """Tests the `clean` method of a validated consent status.

    - VALIDATED to AWAITING is not authorized.
    - VALIDATED to REVOKED with allowed fields is authorized.
    - VALIDATED to REVOKED with not-allowed fields is not authorized.
    - VALIDATED with mixed fields is not authorized.
    """
    from apps.consent.models import Consent

    # update the status from VALIDATED to AWAITING raise exception
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = AWAITING
    with pytest.raises(
        ConsentWorkflowError,
        match='Validated consent can only be changed to the status "revoked".',
    ):
        consent.clean()

    # update the status from VALIDATED to REVOKED with allowed fields is authorized.
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = REVOKED
    consent.revoked_at = FAKE_TIME
    consent.clean()
    consent.save()
    assert consent.status == REVOKED
    assert consent.revoked_at is not None

    # update status VALIDATED to REVOKED with not-allowed field raise exception
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = REVOKED
    # update of an unauthorized field
    consent.end = FAKE_TIME
    with pytest.raises(
        ConsentWorkflowError,
        match="['Only the authorized fields (revoked_at, status, updated_at) can be "
        "modified.']",
    ):
        consent.clean()

    # update status with mixed fields raise exception
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    # update of an unauthorized field
    consent.end = FAKE_TIME
    with pytest.raises(
        ConsentWorkflowError,
        match='Validated consent can only be changed to the status "revoked".',
    ):
        consent.clean()


@pytest.mark.django_db
def test_clean_revoked_consent_status():
    """Tests the `clean` method of a revoked consent status.

    - REVOKED to AWAITING is authorized.
    - REVOKED to VALIDATED is authorized.
    - REVOKED with mixed fields is authorized.
    """
    from apps.consent.models import Consent

    # update the status from REVOKED to AWAITING
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = AWAITING
    consent.clean()
    consent.save()
    assert consent.status == AWAITING

    # update the status from REVOKED to VALIDATED
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.status = VALIDATED
    consent.clean()
    consent.save()
    assert consent.status == VALIDATED

    # update status with mixed fields
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    consent.end = FAKE_TIME
    consent.clean()
    consent.save()
    assert consent.status == REVOKED
    assert consent.end == FAKE_TIME


@pytest.mark.django_db
def test_is_deletion_allowed():
    """Tests the `_is_deletion_allowed` method of a validated consent.

    - AWAITING can be deleted.
    - VALIDATED cannot be deleted.
    - REVOKED cannot be deleted.
    """
    from apps.consent.models import Consent

    # Delete AWAITING consent
    consent = ConsentFactory(status=AWAITING)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    assert consent._is_deletion_allowed() is True

    # Delete VALIDATED consent
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory

    with pytest.raises(
        ConsentWorkflowError, match="Validated consent cannot be deleted."
    ):
        consent._is_deletion_allowed()

    # Delete REVOKED consent
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    with pytest.raises(
        ConsentWorkflowError, match="Revoked consent cannot be deleted."
    ):
        consent._is_deletion_allowed()


@pytest.mark.django_db
def test_delete_consent():
    """Tests deleting a consent.

    - AWAITING can be deleted.
    - VALIDATED cannot be deleted.
    - REVOKED cannot be deleted.
    """
    from apps.consent.models import Consent

    signals.post_save.disconnect(
        receiver=handle_new_delivery_point,
        sender=DeliveryPoint,
        dispatch_uid="handle_new_delivery_point",
    )

    # delete an AWAITING consent
    consent = ConsentFactory(status=AWAITING)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    assert Consent.objects.count() == 1
    assert consent.status == AWAITING
    consent.delete()
    assert Consent.objects.count() == 0

    # delete an VALIDATED consent it is not allowed.
    consent = ConsentFactory(status=VALIDATED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    assert Consent.objects.count() == 1
    assert consent.status == VALIDATED
    with pytest.raises(
        ConsentWorkflowError, match="Validated consent cannot be deleted."
    ):
        consent.delete()
    assert Consent.objects.count() == 1

    # delete an REVOKED consent it is not allowed.
    consent = ConsentFactory(status=REVOKED)
    consent = Consent.objects.get(id=consent.id)  # refresh the state in memory
    expected_consent_number = 2
    assert Consent.objects.count() == expected_consent_number
    assert consent.status == REVOKED
    with pytest.raises(
        ConsentWorkflowError, match="Revoked consent cannot be deleted."
    ):
        consent.delete()
    assert Consent.objects.count() == expected_consent_number

    signals.post_save.connect(
        receiver=handle_new_delivery_point,
        sender=DeliveryPoint,
        dispatch_uid="handle_new_delivery_point",
    )
