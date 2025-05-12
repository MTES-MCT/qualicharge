"""Consent management notif opening renewable metters submission commands."""

import sentry_sdk

from apps.core.management.commands.base_command import DashboardBaseCommand
from apps.core.models import Entity
from apps.renewable.helpers import send_notification_for_opening


class Command(DashboardBaseCommand):
    """Command for sending notifications for the opening of meter reading submission."""

    help = __doc__

    def handle(self, *args, **options):
        """Executes the command for sending notifications."""
        self.notif_opening()

    def notif_opening(self) -> None:
        """Send notifications for the opening of meter reading submission."""
        self._log_notice(
            "⚡ Sending notifications for the opening of meter reading submission..."
        )

        entities = Entity.objects.all()

        for entity in entities:
            self._log_notice(f"⚙️ Processing SIRET: {entity.siret}...")
            try:
                send_notification_for_opening(entity)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                self._log_error(f"Failed to process SIRET: {entity.siret}. Error: {e}")

        self._log_success("✅ Done.")
