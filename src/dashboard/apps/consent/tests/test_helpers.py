"""Dashboard consent helpers tests."""

import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.auth.factories import UserFactory
from apps.consent.helpers import (
    _get_checking_date,
    _get_renewal_end_date,
    send_notification_for_awaiting_consents,
)
from apps.consent.models import Consent
from apps.core.factories import DeliveryPointFactory, EntityFactory
from apps.core.models import Entity


@pytest.mark.django_db
@patch("apps.consent.helpers.send_mail", return_value=1)
def test_send_notification_for_awaiting_consents(mock_send_mail, settings):
    """Test send_notification_for_awaiting_consents."""
    expected_template_id = 6
    expected_link = "https://example.com/consent"
    expected_support = "support@example.com"

    # setup email config
    settings.CONTACT_EMAIL = expected_support
    settings.DASHBOARD_EMAIL_AWAITING_EMAIL = "awaiting_email"
    settings.DASHBOARD_EMAIL_CONFIGS = {
        "awaiting_email": {
            "template_id": expected_template_id,
            "link": expected_link,
        }
    }

    # create, users, entity and consents
    assert Entity.objects.count() == 0
    assert Consent.objects.count() == 0
    user = UserFactory(email="user@example.com")
    user2 = UserFactory(email="")
    entity = EntityFactory(users=[user, user2])
    dp_size = 2
    DeliveryPointFactory.create_batch(dp_size, entity=entity)
    assert Entity.objects.count() == 1
    assert Consent.objects.count() == dp_size

    with patch("apps.consent.helpers.sentry_sdk.capture_message") as mock_sentry:
        # test sending notifications
        send_notification_for_awaiting_consents(entity)

        # notification sending should be called once with only
        # the first user information.
        mock_send_mail.assert_called_once_with(
            [user.email],
            expected_template_id,
            {
                user.email: {
                    "last_name": user.last_name,
                    "first_name": user.first_name,
                    "link": expected_link,
                    "support_email": expected_support,
                }
            },
        )

        # user2 has no email, an error should be raised
        mock_sentry.assert_any_call(
            f"Email can't be send. User {user2.id} does not have an email address.",
            level="error",
        )


@pytest.mark.django_db
@patch("apps.consent.helpers.send_mail", return_value=1)
def test_send_notification_for_no_awaiting_consents(mock_send_mail):
    """Test that no notification is sent if there is no pending consent."""
    # create, users and entity but no consents
    assert Entity.objects.count() == 0
    assert Consent.objects.count() == 0
    entity = EntityFactory()
    assert Entity.objects.count() == 1
    assert Consent.objects.count() == 0

    # no notification should be sent
    send_notification_for_awaiting_consents(entity)
    mock_send_mail.assert_not_called()


@pytest.mark.django_db
def test_get_renewal_end_date_with_number_days(patch_datetime_now, monkeypatch):
    """Test `_get_renewal_end_date` with number days.

    Test function `_get_renewal_end_date` when CONSENT_NUMBER_DAYS_END_DATE is provided.
    """
    days = 90
    monkeypatch.setattr("apps.consent.helpers.CONSENT_NUMBER_DAYS_END_DATE", days)

    renewal_end_date = _get_renewal_end_date()
    expected_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=days
    )
    assert renewal_end_date == expected_date


@pytest.mark.django_db
def test__get_renewal_end_date_without_number_days(patch_datetime_now):
    """Test `_get_renewal_end_date` without number days.

    Test `_get_renewal_end_date` when no CONSENT_NUMBER_DAYS_END_DATE is provided.
    """
    duplicate_date = _get_renewal_end_date()
    current_year = datetime.datetime.now().year
    expected_date = datetime.datetime(
        year=current_year + 1,
        month=12,
        day=31,
        hour=23,
        minute=59,
        second=59,
        tzinfo=datetime.timezone.utc,
    )
    assert duplicate_date == expected_date


@pytest.mark.django_db
def test_get_checking_date_with_upcoming_days_limit(patch_timezone_now, monkeypatch):
    """Test `consent_checking_date` with a provided CONSENT_UPCOMING_DAYS_LIMIT."""
    upcoming_days = 15
    monkeypatch.setattr(
        "apps.consent.helpers.CONSENT_UPCOMING_DAYS_LIMIT", upcoming_days
    )

    now = timezone.now()
    expected_date = now.replace(
        hour=23, minute=59, second=59, microsecond=999999
    ) + datetime.timedelta(days=upcoming_days)

    assert _get_checking_date() == expected_date
