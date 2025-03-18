"""Dashboard consent command notif awaiting consents tests."""

from unittest.mock import MagicMock, patch

import pytest

from apps.consent.management.commands.notifawaitingconsents import Command
from apps.core.factories import EntityFactory
from apps.core.models import Entity


@pytest.mark.django_db
def test_notif_awaiting_consents_invoked_on_entities(monkeypatch):
    """Tests that the command is invoked on entities."""
    # Create entities
    assert Entity.objects.all().count() == 0
    entity_1 = EntityFactory()
    entity_2 = EntityFactory()
    expected_entities_count = 2
    assert Entity.objects.all().count() == expected_entities_count

    mock_send_notif = MagicMock()
    monkeypatch.setattr(
        "apps.consent.management.commands.notifawaitingconsents.send_notification_for_awaiting_consents",
        mock_send_notif,
    )

    # Execute command
    command = Command()
    command.notif_awaiting_consents()

    # Ensure the mocked send_notification_for_awaiting_consents was called
    # for both entities.
    assert mock_send_notif.call_count == expected_entities_count
    mock_send_notif.assert_any_call(entity_1)
    mock_send_notif.assert_any_call(entity_2)


@pytest.mark.django_db
@patch(
    "apps.consent.management.commands.notifawaitingconsents.send_notification_for_awaiting_consents"
)
def test_notif_awaiting_consents_handles_exception(mock_send_notif):
    """Tests that the command handles exceptions raised by the func."""
    assert Entity.objects.all().count() == 0
    EntityFactory()
    assert Entity.objects.all().count() == 1

    # setup send_notification_for_awaiting_consents raise an exception
    mock_send_notif.side_effect = Exception("Send notification error")

    with patch("sentry_sdk.capture_exception") as mock_capture_exception:
        # Execute command
        command = Command()
        command.notif_awaiting_consents()

        # Checks that the mocked method was called, and the exception was caught.
        mock_send_notif.assert_called_once()
        mock_capture_exception.assert_called_once()


@pytest.mark.django_db
@patch(
    "apps.consent.management.commands.notifawaitingconsents.send_notification_for_awaiting_consents"
)
def test_notif_awaiting_consents_with_no_entities(mock_send_notif):
    """Tests that the command is not called when there are no entities."""
    assert Entity.objects.all().count() == 0

    # Run the command with no entities
    command = Command()
    command.notif_awaiting_consents()

    # Check that the func is never called
    mock_send_notif.assert_not_called()
