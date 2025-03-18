"""Consent management notif awaiting consents commands."""

import sentry_sdk

from apps.consent.helpers import send_notification_for_awaiting_consents
from apps.core.management.commands.base_command import DashboardBaseCommand
from apps.core.models import Entity


class Command(DashboardBaseCommand):
    """Command for sending notifications for awaiting consents."""

    help = __doc__

    def handle(self, *args, **options):
        """Executes the command for sending notifications for awaiting consents."""
        self.notif_awaiting_consents()

    def notif_awaiting_consents(self) -> None:
        """Send notifications for awaiting consents."""
        self._log_notice("⚡ Sending notifications for awaiting consents...")

        entities = Entity.objects.all()

        for entity in entities:
            self._log_notice(f"⚙️ Processing SIRET: {entity.siret}...")
            try:
                send_notification_for_awaiting_consents(entity)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                self._log_error(f"Failed to process SIRET: {entity.siret}. Error: {e}")

        self._log_success("✅ Done.")
