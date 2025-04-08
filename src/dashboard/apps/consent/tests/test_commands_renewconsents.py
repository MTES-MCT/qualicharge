"""Dashboard consent command duplicates consents tests."""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.consent import AWAITING, VALIDATED
from apps.consent.helpers import renew_expiring_consents
from apps.consent.management.commands.renewconsents import Command
from apps.consent.models import Consent
from apps.core.factories import DeliveryPointFactory


def _create_consent(
    start: datetime.datetime, end: datetime.datetime, status: str | None = None
) -> Consent:
    """Create a consent for a delivery point."""
    dp = DeliveryPointFactory.create()
    consent = Consent.objects.get(delivery_point=dp)
    consent.start = start
    consent.end = end

    if status is not None:
        consent.status = status

    consent.save()

    return consent


@pytest.mark.django_db
def test_renew_expiring_consents_without_consents():
    """Tests the `renew_expiring_consents` command without consents don't fail."""
    assert Consent.objects.count() == 0
    renew_expiring_consents()
    assert Consent.objects.count() == 0


@pytest.mark.django_db
def test_renew_expiring_consents_outside_period(monkeypatch):
    """Tests the `renew_expiring_consents` command outside the period.

    This consent should not be renewed.
    """
    # mock now() to be the 2025-12-28.
    fake_time = datetime.datetime(2025, 12, 28, tzinfo=datetime.timezone.utc)
    monkeypatch.setattr("django.utils.timezone.now", lambda: fake_time)

    # create a consent outside the active period
    start = datetime.datetime(2026, 1, 15, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(2026, 3, 15, tzinfo=datetime.timezone.utc)
    assert Consent.objects.count() == 0
    _create_consent(start, end)
    assert Consent.objects.count() == 1
    assert Consent.active_objects.count() == 0

    # test renew_expiring_consents()
    duplicated_consents = renew_expiring_consents()
    assert len(duplicated_consents) == 0
    assert Consent.objects.count() == 1


@pytest.mark.django_db
def test_renew_expiring_consents(monkeypatch, settings):  # noqa: PLR0915
    """Tests the `renew_expiring_consents`."""
    settings.CONSENT_UPCOMING_DAYS_LIMIT = 30

    # default consent start period
    start_date = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)

    # default end period date for the duplicated consents (for the futur period)
    futur_period_end_date = datetime.datetime(
        2026, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc
    )

    # create 2 validated consents - period: 2025-01-01 to 2025-12-31
    consent_size = 2
    DeliveryPointFactory.create_batch(consent_size)
    for consent in Consent.objects.all():
        consent.start = start_date
        consent.end = datetime.datetime(
            2025, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc
        )
        consent.status = VALIDATED
        consent.save()
    assert Consent.objects.count() == consent_size
    assert Consent.active_objects.count() == consent_size
    assert Consent.validated_objects.count() == consent_size

    # create a validated consent with an end date is in 30 days
    # period: 2025-01-01 to 2025-11-15.
    end = datetime.datetime(2025, 12, 15, 1, 5, 55, 0, tzinfo=datetime.timezone.utc)
    _create_consent(start_date, end, VALIDATED)
    assert Consent.objects.count() == 3  # noqa: PLR2004
    assert Consent.active_objects.count() == 3  # noqa: PLR2004
    assert Consent.validated_objects.count() == 3  # noqa: PLR2004

    # Create an awaiting consent - it should not be renewed.
    # period: 2025-01-01 to 2025-12-31.
    end = datetime.datetime(2025, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
    _create_consent(start_date, end, AWAITING)
    assert Consent.objects.count() == 4  # noqa: PLR2004
    assert Consent.active_objects.count() == 4  # noqa: PLR2004
    assert Consent.validated_objects.count() == 3  # noqa: PLR2004
    assert Consent.active_objects.filter(status=AWAITING).count() == 1

    # create 2 consents (a validated consent with its renewed equivalent)
    end = datetime.datetime(2025, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
    consent_with_duplicated = _create_consent(start_date, end, VALIDATED)
    Consent.objects.create(
        delivery_point=consent_with_duplicated.delivery_point,
        provider_assigned_id=consent_with_duplicated.provider_assigned_id,
        start=consent_with_duplicated.end,
        end=futur_period_end_date,
    )
    assert Consent.objects.count() == 6  # noqa: PLR2004
    assert Consent.active_objects.count() == 5  # noqa: PLR2004
    assert Consent.validated_objects.count() == 4  # noqa: PLR2004
    assert Consent.active_objects.filter(status=AWAITING).count() == 1

    # test renew_expiring_consents()
    # 1- mock now() to be before the consents to be duplicated.
    fake_time = datetime.datetime(2025, 3, 31, tzinfo=datetime.timezone.utc)
    monkeypatch.setattr("django.utils.timezone.now", lambda: fake_time)

    # no consents should be renewed
    duplicated_consents = renew_expiring_consents()
    assert len(duplicated_consents) == 0
    assert Consent.objects.count() == 6  # noqa: PLR2004

    # 2 -mock now() to be the 2025-12-14
    fake_time = datetime.datetime(2025, 12, 14, tzinfo=datetime.timezone.utc)
    monkeypatch.setattr("django.utils.timezone.now", lambda: fake_time)

    # test renew_expiring_consents() - 3 consents should be renewed.
    duplicated_consents = renew_expiring_consents()
    assert len(duplicated_consents) == 3  # noqa: PLR2004
    for duplicated, consent in zip(
        duplicated_consents,
        Consent.validated_objects.filter().exclude(id=consent_with_duplicated.id),
        strict=True,
    ):
        assert duplicated.provider_assigned_id == consent.provider_assigned_id
        assert duplicated.start == consent.end
        assert duplicated.end == futur_period_end_date

    # 6 active objects + 3 renewed consents
    assert Consent.objects.count() == 9  # noqa: PLR2004

    # 3 - create a new consent that would have been missed (ie: it was added after
    # the cron passed). Period: 2025-01-01 to 2025-12-17.
    end = datetime.datetime(2025, 12, 17, 23, tzinfo=datetime.timezone.utc)
    consent = _create_consent(start_date, end, VALIDATED)
    assert Consent.objects.count() == 10  # noqa: PLR2004
    assert Consent.active_objects.count() == 6  # noqa: PLR2004

    # test renew_expiring_consents() - 1 consent should be renewed.
    duplicated_consents = renew_expiring_consents()

    assert len(duplicated_consents) == 1
    assert Consent.objects.count() == 11  # noqa: PLR2004
    assert duplicated_consents[0].provider_assigned_id == consent.provider_assigned_id
    assert duplicated_consents[0].start == end
    assert duplicated_consents[0].end == futur_period_end_date


@pytest.mark.django_db
def test_handle_generates_missing_consents(monkeypatch):
    """Test the `handle` method calls `generate_missing_consents` successfully."""
    mock_generate = MagicMock()
    monkeypatch.setattr(
        "apps.consent.management.commands.renewconsents.generate_missing_consents",
        mock_generate,
    )

    command = Command()
    command.handle()
    mock_generate.assert_called_once_with()


@pytest.mark.django_db
def test_handle_handles_exceptions(monkeypatch):
    """Test `handle` method captures and logs exceptions during execution."""
    mock_generate = MagicMock()
    monkeypatch.setattr(
        "apps.consent.management.commands.renewconsents.generate_missing_consents",
        mock_generate,
    )

    mock_generate.side_effect = Exception("Error")

    with patch("sentry_sdk.capture_exception") as mock_capture_exception:
        command = Command()
        command.handle()
        mock_generate.assert_called_once_with()

        mock_capture_exception.assert_called_once()
