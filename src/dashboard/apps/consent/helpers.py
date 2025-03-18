"""Dashboard consent helpers."""

import sentry_sdk
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import AnymailMessage
from django.conf import settings

from apps.core.models import Entity


def send_notification_for_awaiting_consents(entity: Entity) -> None:
    """Send notification for awaiting consents for a given entity.

    Sends email notifications to users associated with the given entity regarding
    awaiting consents.

    Parameters:
        entity (Entity): The entity for which awaiting consent notifications need
        to be sent.

    Raises:
        Captures error information via a logging system for users without a valid
        email address.
    """
    if entity.count_awaiting_consents() == 0:
        return

    email_config = settings.DASHBOARD_EMAIL_CONFIGS[
        settings.DASHBOARD_EMAIL_AWAITING_EMAIL
    ]
    template_id: int = email_config["template_id"]

    recipients: list = []
    email_data: dict = {}

    for user in entity.users.all():
        if not user.email:
            error = (
                f"Email can't be send. User {user.id} does not have an email address."
            )
            sentry_sdk.capture_message(error, level="error")
            continue

        recipients.append(user.email)
        email_data[user.email] = {
            "last_name": user.last_name,
            "first_name": user.first_name,
            "link": email_config.get("link"),
            "support_email": settings.CONTACT_EMAIL,
        }

    send_mail(recipients, template_id, email_data)


def send_mail(recipients: list, template_id: int, email_data: dict) -> int | None:
    """Send an email to the recipients.

    Returns:
        int: Number of successfully sent emails or 0 if sending fails.
    """
    if not recipients:
        # Log a warning to Sentry if no recipients are found
        error = "Email can't be sent. No recipients with valid email addresses."
        sentry_sdk.capture_message(error, level="warning")
        return 0

    email = AnymailMessage(
        to=recipients,
        template_id=template_id,
        merge_data=email_data,
    )

    try:
        return email.send()
    except AnymailRequestsAPIError as e:
        # fail silently and send a sentry log
        sentry_sdk.capture_exception(e)
        return 0
