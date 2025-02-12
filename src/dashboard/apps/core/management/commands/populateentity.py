"""Core management commands."""

from django.core.management.base import BaseCommand

from apps.core.helpers import sync_entity_from_siret


class Command(BaseCommand):
    """Populate an entity with data from the API `annuaire des entreprises`.

    Note: this command is actually meant to be used in dev only.
    """

    help = __doc__

    def add_arguments(self, parser):
        """Add arguments to the command."""
        parser.add_argument("siret", type=str)

    def handle(self, *args, **options):
        """Executes the command for populating an entity."""
        self.stdout.write(
            self.style.WARNING("this command is actually meant to be used in dev only.")
        )
        self.stdout.write(
            self.style.NOTICE(
                'Querying "Annuaire des Entreprises" API and populating entity...'
            )
        )
        sync_entity_from_siret(siret=options["siret"])
        self.stdout.write(self.style.SUCCESS("Done."))
