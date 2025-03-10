"""Dashboard auth mails."""

import sentry_sdk
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import AnymailMessage
from django.conf import settings
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _


def send_validation_email(users) -> None:
    """Send a validation email to one or many the user."""
    email_config = settings.DASHBOARD_EMAIL_CONFIGS["validated_user"]

    if not isinstance(users, QuerySet):
        users = [users]

    recipients = []
    email_data = {}
    for user in users:
        if not user.email:
            raise ValueError(
                _(
                    f"Email can't be send. "
                    f"User {user} does not have an email address."
                )
            )

        recipients.append(user.email)
        email_data[user.email] = {
            "last_name": user.last_name,  # type: ignore[union-attr]
            "first_name": user.first_name,  # type: ignore[union-attr]
            "link": email_config.get("link"),
            "support_email": settings.CONTACT_EMAIL,
        }

    email = AnymailMessage(
        to=recipients,
        template_id=email_config.get("template_id"),
        merge_data=email_data,
    )

    try:
        email.send()
    except AnymailRequestsAPIError as e:
        # fail silently and send a sentry log
        sentry_sdk.capture_exception(e)
