"""Consent management duplicate consents commands."""

import sentry_sdk

from apps.consent.helpers import renew_expiring_consents
from apps.core.management.commands.base_command import DashboardBaseCommand


class Command(DashboardBaseCommand):
    """Command for renewing expiring consents."""

    help = __doc__

    def handle(self, *args, **options):
        """Renew expiring consents that are nearing expiration.

        This method attempts to duplicate expiring
        consents and logs an error message if the operation fails.

        Raises:
            Exception: Captures any exception occurring during the consent
            duplication process and logs the error, including the relevant SIRET and
            error details.
        """
        try:
            renew_expiring_consents()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            self._log_error(f"Failed to duplicate consents. Error: {e}")
