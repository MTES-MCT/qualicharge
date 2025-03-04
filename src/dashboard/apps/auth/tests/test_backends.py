"""Dashboard consent backends tests."""

from unittest.mock import patch

import pytest
from anymail.exceptions import AnymailRequestsAPIError
from django.conf import settings
from django.urls import reverse

from apps.auth.backends import OIDCAuthenticationBackend
from apps.auth.factories import UserFactory


@pytest.mark.django_db
def test_send_email_notification_populated(rf):
    """Test `_send_email` is sent."""
    user = UserFactory()
    backend = OIDCAuthenticationBackend()

    with patch("apps.auth.backends.AnymailMessage") as mock_message:
        email_send_mock = mock_message.return_value.send
        backend._send_email(user)

        expected_email_config = settings.DASHBOARD_EMAIL_CONFIGS["new_subscription"]
        expected_email_to = settings.CONTACT_EMAIL
        mock_message.assert_called_once_with(
            to=[
                expected_email_to,
            ],
            template_id=expected_email_config.get("template_id"),
            merge_data={
                expected_email_to: {
                    "user_last_name": user.last_name,
                    "user_first_name": user.first_name,
                    "user_email": user.email,
                    "link": reverse(
                        "admin:qcd_auth_dashboarduser_change", args=(user.id,)
                    ),
                }
            },
        )
        email_send_mock.assert_called_once()


@pytest.mark.django_db
def test_send_email_raises_exception_logged_to_sentry(rf):
    """Test `_send_email` handles exception and logs it to Sentry."""
    user = UserFactory()
    backend = OIDCAuthenticationBackend()

    with patch("apps.auth.backends.AnymailMessage") as mock_message:
        mock_message.return_value.send.side_effect = AnymailRequestsAPIError()

        with patch("apps.auth.backends.sentry_sdk.capture_exception") as mock_sentry:
            backend._send_email(user)
            mock_sentry.assert_called_once()
