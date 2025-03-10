"""Dashboard auth mails tests."""

from unittest.mock import patch

import pytest
from anymail.exceptions import AnymailRequestsAPIError
from django.conf import settings

from apps.auth.factories import UserFactory
from apps.auth.mails import send_validation_email
from apps.auth.models import DashboardUser


@pytest.mark.django_db
def test_send_validation_email_success():
    """Test `send_validation_email` successfully sends an email."""
    user1 = UserFactory(email="user1@example.com")
    user2 = UserFactory(email="user2@example.com")

    # test send notification to one user
    with patch("apps.auth.mails.AnymailMessage") as mock_message:
        email_send_mock = mock_message.return_value.send
        send_validation_email(user1)

        expected_email_config = settings.DASHBOARD_EMAIL_CONFIGS["validated_user"]
        mock_message.assert_called_once_with(
            to=["user1@example.com"],
            template_id=expected_email_config.get("template_id"),
            merge_data={
                "user1@example.com": {
                    "last_name": user1.last_name,
                    "first_name": user1.first_name,
                    "link": expected_email_config.get("link"),
                    "support_email": settings.CONTACT_EMAIL,
                },
            },
        )
        email_send_mock.assert_called_once()

    # test send notification to many users (querysets)
    users = DashboardUser.objects.all()
    expected_users_count = 2
    assert users.count() == expected_users_count

    with patch("apps.auth.mails.AnymailMessage") as mock_message:
        email_send_mock = mock_message.return_value.send
        send_validation_email(users)

        expected_email_config = settings.DASHBOARD_EMAIL_CONFIGS["validated_user"]
        mock_message.assert_called_once_with(
            to=["user1@example.com", "user2@example.com"],
            template_id=expected_email_config.get("template_id"),
            merge_data={
                "user1@example.com": {
                    "last_name": user1.last_name,
                    "first_name": user1.first_name,
                    "link": expected_email_config.get("link"),
                    "support_email": settings.CONTACT_EMAIL,
                },
                "user2@example.com": {
                    "last_name": user2.last_name,
                    "first_name": user2.first_name,
                    "link": expected_email_config.get("link"),
                    "support_email": settings.CONTACT_EMAIL,
                },
            },
        )
        email_send_mock.assert_called_once()


@pytest.mark.django_db
def test_send_validation_email_without_user_mail_raise_value_error():
    """Test `send_validation_email` raises ValueError when user has no email."""
    user1 = UserFactory(email="")
    UserFactory(email="user2@example.com")

    # test send notification to one user
    with pytest.raises(
        ValueError,
        match=f"Email can't be send. User {user1} does not have an email address.",
    ):
        send_validation_email(user1)

    # test send notification to many users (querysets)
    users = DashboardUser.objects.all()
    expected_users_count = 2
    assert users.count() == expected_users_count
    with pytest.raises(
        ValueError,
        match=f"Email can't be send. User {user1} does not have an email address.",
    ):
        send_validation_email(users)


@pytest.mark.django_db
def test_send_validation_email_handles_exception():
    """Test `send_validation_email` handles email sending exception."""
    user = UserFactory(email="testuser@example.com")

    with patch("apps.auth.mails.AnymailMessage") as mock_message:
        mock_message.return_value.send.side_effect = AnymailRequestsAPIError()
        with patch("apps.auth.mails.sentry_sdk.capture_exception") as mock_sentry:
            send_validation_email(user)
            mock_sentry.assert_called_once()
