"""Consent management commands."""

from django.core.management.base import BaseCommand

from apps.consent.fixtures.consent import seed_consent


class Command(BaseCommand):
    """Create development fixtures for the consent management system."""

    help = __doc__

    def handle(self, *args, **kwargs):
        """Executes the command for creating development consent fixtures."""
        self.stdout.write(self.style.NOTICE("Seeding database with consents..."))
        seed_consent()
        self.stdout.write(
            self.style.SUCCESS("Done.")
        )
