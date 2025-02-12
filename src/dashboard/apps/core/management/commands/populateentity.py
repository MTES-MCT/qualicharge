"""Core management commands."""

import sentry_sdk
from django.core.management.base import BaseCommand

from apps.core.helpers import sync_entity_from_siret


class Command(BaseCommand):
    """Populate an entity with data from the API `annuaire des entreprises`.

    Note: this command is actually meant to be used in dev only.
    """

    help = __doc__

    def add_arguments(self, parser):
        """Add arguments to the command."""
        # parser.add_argument("siret", type=list)
        parser.add_argument(
            "siret",
            nargs="+",
            type=str,
            help="One or more SIRET numbers to populate entities from the API.",
        )

    def handle(self, *args, **options):
        """Executes the command for populating an entity."""
        self.stderr.write(
            self.style.WARNING("this command is actually meant to be used in dev only.")
        )
        self.stderr.write(
            self.style.NOTICE(
                'Querying "Annuaire des Entreprises" API and populating entity...'
            )
        )
        for siret in options["siret"]:
            self.stderr.write(self.style.NOTICE(f"Processing SIRET: {siret}..."))
            try:
                sync_entity_from_siret(siret)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                self.stderr.write(
                    self.style.ERROR(
                        f"Error during processing SIRET: {siret}. {e}",
                    )
                )

        self.stderr.write(self.style.SUCCESS("Done."))
