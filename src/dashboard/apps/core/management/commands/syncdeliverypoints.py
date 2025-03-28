"""Core management sync delivery points commands."""

from typing import List, Optional

import sentry_sdk
from django.db.models import QuerySet

from apps.consent.helpers import send_notification_for_awaiting_consents
from apps.consent.models import Consent
from apps.core.helpers import sync_delivery_points_from_qualicharge_api
from apps.core.management.commands.base_command import DashboardBaseCommand
from apps.core.models import DeliveryPoint, Entity


class Command(DashboardBaseCommand):
    """Synchronize delivery points using QualiCharge API.

    Synchronizes delivery points by querying the external "QualiCharge" API and
    updating related data for all entities in the database.

    This method fetches all the entities, processes each entity by updating its
    delivery points data from the "QualiCharge" API.
    If any error occurs during the synchronization process for a specific entity,
    the exception is logged using Sentry and an error message is displayed.

    Raises:
        Exception: Captures any exceptions encountered during the processing of
        an entity.
    """

    help = __doc__

    def add_arguments(self, parser):
        """Add optional `siret` argument to the command."""
        parser.add_argument(
            "siret",
            nargs="*",
            type=str,
            help="One or more SIRET numbers to populate entities from the API.",
        )

    def handle(self, *args, **options):
        """Executes the command for syncing delivery points."""
        self.sync_delivery_points(options["siret"])

    def sync_delivery_points(self, siret: list[str] | None = None) -> None:
        """Sync delivery points from QCC API."""
        self._log_notice(
            '⚡ Querying "QualiCharge" API and updating delivery points...'
        )

        delivery_points: List[DeliveryPoint] = []
        consents: Optional[List[Consent]] = []

        entities: QuerySet = (
            Entity.objects.filter(siret__in=siret) if siret else Entity.objects.all()
        )

        for entity in entities:
            self._log_notice(f"⚙️ Processing SIRET: {entity.siret}...")
            try:
                delivery_points, consents = sync_delivery_points_from_qualicharge_api(
                    entity
                )
            except Exception as e:
                sentry_sdk.capture_exception(e)
                self._log_error(
                    f"- Failed to process SIRET: {entity.siret}. Error: {e}"
                )

            self._log_notice(f"- {len(delivery_points)} delivery point(s) created")

            if consents:
                send_notification_for_awaiting_consents(entity)

        self._log_success("\n✅ Sync completed successfully.")
