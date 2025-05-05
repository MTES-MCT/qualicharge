"""Dashboard core mail helpers."""

import sentry_sdk
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import AnymailMessage


def send_mail(recipients: list, template_id: int, email_data: dict) -> int | None:
    """Sends an email using AnymailMessage.

    The function logs a warning and fails silently if any errors are encountered during
    the email sending process.

    Args:
        recipients (list): A list of recipients' email addresses.
        template_id (int): The template ID (from Brevo) to use for the email.
        email_data (dict): Data to be merged with the email template.

    Returns:
        int | None: The number of emails sent successfully, or 0 if an error occurs or
        no recipients are provided.
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
