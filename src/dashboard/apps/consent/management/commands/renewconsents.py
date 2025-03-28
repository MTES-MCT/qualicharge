"""Consent management duplicate and generate missing consents commands."""

import sentry_sdk

from apps.consent.helpers import generate_missing_consents, renew_expiring_consents
from apps.core.management.commands.base_command import DashboardBaseCommand


class Command(DashboardBaseCommand):
    """Command for renewing expiring consents."""

    help = __doc__

    def handle(self, *args, **options):
        """Renew expiring consents that are nearing expiration and generate new ones.

        This method attempts to
        - duplicate expiring consents and logs an error message if the operation fails.
        - generate new consents for delivery points that do not have active consents.

        Raises:
            Exception: Captures any exception occurring during the consent
            duplication process and logs the error, including the relevant SIRET and
            error details.
        """
        expiring_consents = consents = []

        try:
            expiring_consents = renew_expiring_consents()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            self._log_error(f"Failed to duplicate consents. Error: {e}")
        self._log_notice(f"Duplicate {len(expiring_consents)} consent(s).")

        try:
            consents = generate_missing_consents()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            self._log_error(f"Failed to generating new consents. Error: {e}")
        self._log_notice(f"Generated {len(consents)} new consent(s).")
