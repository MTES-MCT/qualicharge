"""Dashboard consent helpers tests."""

from unittest.mock import patch

import pytest

from apps.auth.factories import UserFactory
from apps.consent.helpers import send_notification_for_awaiting_consents
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
