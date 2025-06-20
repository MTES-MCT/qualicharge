"""Renewable management commands."""

from django.core.management.base import BaseCommand

from ...fixtures.renewable import seed_renewable


class Command(BaseCommand):
    """Create development fixtures for the renewable management system."""

    help = __doc__

    def handle(self, *args, **kwargs):
        """Executes the command for creating development renewable fixtures."""
        self.stdout.write(self.style.NOTICE("Seeding database with renewables..."))
        seed_renewable()
        self.stdout.write(self.style.SUCCESS("Done."))
