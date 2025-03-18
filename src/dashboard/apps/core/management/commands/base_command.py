"""Consent management base command."""

from django.core.management.base import BaseCommand


class DashboardBaseCommand(BaseCommand):
    """Mixin providing helper methods for logging messages in management commands."""

    def _log_notice(self, message: str) -> None:
        """Helper method for logging notice messages."""
        self.stderr.write(self.style.NOTICE(message))

    def _log_success(self, message: str) -> None:
        """Helper method for logging success messages."""
        self.stderr.write(self.style.SUCCESS(message))

    def _log_error(self, message: str) -> None:
        """Helper method for logging error messages."""
        self.stderr.write(self.style.ERROR(message))
