"""Dashboard consent app settings."""

from django.conf import settings

# CONSENT_NUMBER_DAYS_END_DATE allows to calculate the end date of a consent period by
# adding a number of days to the current date.
# If the value is None, the end date of the period will correspond to the last day of
# the current year
# More details on the calculation in the function: `utils.consent_end_date()`
# ie:
# CONSENT_NUMBER_DAYS_END_DATE = 90 will return the current date + 90 days.
# CONSENT_NUMBER_DAYS_END_DATE = None will return 2024-12-31 23:59:59 (if calculated
# during the year 2024).
CONSENT_NUMBER_DAYS_END_DATE = getattr(settings, "CONSENT_NUMBER_DAYS_END_DATE", None)

# Control authority contact for consent validation.
CONSENT_CONTROL_AUTHORITY = getattr(
    settings,
    "CONSENT_CONTROL_AUTHORITY",
    {
        "name": "<administration name>",
        "address_1": "<Adresse 1>",
        "address_2": "<Adresse complement>",
        "zip_code": "92000",
        "city": "<city>",
        "represented_by": "<represented by>",
        "email": "<email@gouv.fr>",
    },
)
CONSENT_SIGNATURE_LOCATION = getattr(settings, "CONSENT_SIGNATURE_LOCATION", "<city>")
