"""Consent management generate missing consents commands."""

import sentry_sdk

from apps.consent.helpers import generate_missing_consents
from apps.core.management.commands.base_command import DashboardBaseCommand


class Command(DashboardBaseCommand):
    """Generating consents for delivery points that do not have active consents."""

    help = __doc__

    def handle(self, *args, **options):
        """Handles the generation of missing consents.

        Raises:
            Exception: Captures any exception raised during the generation of missing
            consents and logs the corresponding error message.
        """
        try:
            consents = generate_missing_consents()
            self._log_notice(f"Generated {len(consents)} new consent(s).")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            self._log_error(f"Failed to generating new consents. Error: {e}")

        self._log_success("✅ Done.")
