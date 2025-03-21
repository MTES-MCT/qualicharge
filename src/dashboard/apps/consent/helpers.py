"""Dashboard consent helpers."""

import datetime

import sentry_sdk
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import AnymailMessage
from django.conf import settings
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.utils import timezone

from apps.consent.models import Consent
from apps.consent.utils import consent_end_date
from apps.core.models import Entity

from .settings import CONSENT_NUMBER_DAYS_END_DATE, CONSENT_UPCOMING_DAYS_LIMIT


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


def renew_expiring_consents():
    """Renew expiring consents to ensure continuity.

    Perform the renewal of expiring consents to ensure continuity for consents that
    are nearing their expiration date and have not been renewed yet.
    The function identifies consents that are set to expire shortly and generates
    new consents starting immediately after the expiry date of the current consent,
    with an extended validity period.

    - Consents should be renewed if their end date is earlier than or equal to
    `now + CONSENT_NUMBER_DAYS_END_DATE`.
    - renewed consent date:
        - start date of new consent is end date of current consent
        - end date of new consent is calculate from CONSENT_NUMBER_DAYS_END_DATE

    Returns:
        List[Consent]: A list of newly created Consent objects that have been renewed
         from the expiring consents.
    """
    # calculate the date from which to check
    checking_date = _get_checking_date()

    # calculate the end date of renewed consents
    renewal_end_date = _get_renewal_end_date()

    # Subquery to check if a renewed consent exists for validated consents.
    # (this subquery only returns the `provider_assigned_id` of the consents found)
    existing_renewed_consents = Consent.objects.filter(
        start__gte=OuterRef("end"),
        delivery_point=OuterRef("delivery_point"),
        id_station_itinerance=OuterRef("id_station_itinerance"),
        station_name=OuterRef("station_name"),
        provider_assigned_id=OuterRef("provider_assigned_id"),
    ).values("provider_assigned_id")

    # Get expiring consents
    #  = all validated consents - validated consents with existing consents.
    # fmt: off
    expiring_consents = (
        Consent.validated_objects
            .exclude(provider_assigned_id__in=Subquery(existing_renewed_consents))
            .filter(end__lte=checking_date)
    )
    # fmt: on

    # create a list of new consents to renewed
    consents_to_renewed = []
    for consent in expiring_consents:
        consents_to_renewed.append(
            Consent(
                delivery_point=consent.delivery_point,
                id_station_itinerance=consent.id_station_itinerance,
                station_name=consent.station_name,
                provider_assigned_id=consent.provider_assigned_id,
                start=consent.end,
                end=renewal_end_date,
            )
        )

    # Create new renewed consents
    results = []
    if consents_to_renewed:
        with transaction.atomic():
            results = Consent.objects.bulk_create(consents_to_renewed)
    return results


def _get_checking_date():
    """Calculate the date from which to check."""
    now = timezone.now()
    end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return end_of_today + datetime.timedelta(days=CONSENT_UPCOMING_DAYS_LIMIT)


def _get_renewal_end_date():
    """Calculate the end date of renewed consents."""
    renewal_end_date = consent_end_date(CONSENT_NUMBER_DAYS_END_DATE)
    if not CONSENT_NUMBER_DAYS_END_DATE:
        renewal_end_date = renewal_end_date.replace(year=renewal_end_date.year + 1)

    return renewal_end_date
