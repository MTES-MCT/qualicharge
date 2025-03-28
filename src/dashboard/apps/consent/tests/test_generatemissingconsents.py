"""Dashboard consent command generating missing consents tests."""

from unittest.mock import MagicMock, patch

import pytest

from apps.consent.management.commands.generatemissingconsents import Command


@pytest.mark.django_db
def test_handle_generates_missing_consents(monkeypatch):
    """Test the `handle` method calls `generate_missing_consents` successfully."""
    mock_generate = MagicMock()
    monkeypatch.setattr(
        "apps.consent.management.commands.generatemissingconsents.generate_missing_consents",
        mock_generate,
    )

    command = Command()
    command.handle()
    mock_generate.assert_called_once_with()


@pytest.mark.django_db
def test_handle_handles_exceptions(monkeypatch):
    """Test `handle` method captures and logs exceptions during execution."""
    mock_generate = MagicMock()
    monkeypatch.setattr(
        "apps.consent.management.commands.generatemissingconsents.generate_missing_consents",
        mock_generate,
    )

    mock_generate.side_effect = Exception("Error")

    with patch("sentry_sdk.capture_exception") as mock_capture_exception:
        command = Command()
        command.handle()
        mock_generate.assert_called_once_with()

        mock_capture_exception.assert_called_once()
