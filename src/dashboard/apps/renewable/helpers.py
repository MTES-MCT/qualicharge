"""Dashboard renewable helpers."""

from datetime import date
from typing import Tuple

import sentry_sdk
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import AnymailMessage
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone

from apps.core.models import Entity
from apps.core.utils import get_current_quarter_date_range

DateRange = Tuple[date, date]


def get_opening_period_dates() -> DateRange:
    """Gets the date range for the renewable opening period.

    This function calculates the starting date and end date of the renewable
    opening period based on the current quarter's beginning date and a configured
    number of days for the opening period.

    The opening period starts on the first day of the quarter and ends `x` days after.

    Returns:
        DateRange: A tuple containing the start and end date of the opening period.

    """
    first_day, _ = get_current_quarter_date_range()
    period_days = settings.RENEWABLE_OPENING_PERIOD_DAYS

    return first_day, first_day + relativedelta(days=period_days - 1)


def is_in_opening_period(reference_date: date) -> bool:
    """Check if the reference_date is in the opening period."""
    start_period, end_period = get_opening_period_dates()
    if start_period <= reference_date <= end_period:
        return True
    return False


def send_notification_for_opening(entity: Entity) -> None:
    """Send notification for opening period for a given entity."""
    if not entity.has_renewable():
        return

    if not is_in_opening_period(timezone.now().date()):
        return

    email_config_key = settings.DASHBOARD_EMAIL_RENEWABLE_OPENING_PERIOD
    email_config = settings.DASHBOARD_EMAIL_CONFIGS[email_config_key]
    template_id: int = email_config["template_id"]

    recipients: list = []
    email_data: dict = {}

    start_period, end_period = get_opening_period_dates()
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
            "support_link": settings.CONTACT_LINK,
            "start_period": start_period.strftime("%d/%m/%Y"),
            "end_period": end_period.strftime("%d/%m/%Y"),
        }

    if not recipients:
        # Log a warning to Sentry if no recipients are found
        error = "Email can't be sent. No recipients with valid email addresses."
        sentry_sdk.capture_message(error, level="warning")
        return

    email = AnymailMessage(
        to=recipients,
        template_id=template_id,
        merge_data=email_data,
    )

    try:
        email.send()
    except AnymailRequestsAPIError as e:
        # fail silently and send a sentry log
        sentry_sdk.capture_exception(e)
        return
