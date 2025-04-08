"""Dashboard core command sync delivery points tests."""

from unittest.mock import MagicMock, patch

import pytest

from apps.core.factories import EntityFactory
from apps.core.management.commands.syncdeliverypoints import Command
from apps.core.models import Entity


@pytest.mark.django_db
def test_sync_delivery_points_invoked_on_entities(monkeypatch):
    """Tests `sync_from_qualicharge_api` is called for each entity."""
    # Create entities
    assert Entity.objects.all().count() == 0
    entity_1 = EntityFactory()
    entity_2 = EntityFactory()
    expected_entities_count = 2
    assert Entity.objects.all().count() == expected_entities_count

    mock_sync = MagicMock()
    monkeypatch.setattr(
        "apps.core.management.commands.syncdeliverypoints.sync_from_qualicharge_api",
        mock_sync,
    )

    # Execute command
    command = Command()
    command.sync_delivery_points()

    # Ensure the mocked sync was called for both entities
    assert mock_sync.call_count == expected_entities_count
    mock_sync.assert_any_call(entity_1)
    mock_sync.assert_any_call(entity_2)

    # Execute command with one siret
    mock_sync.reset_mock()
    command.sync_delivery_points([entity_1.siret])

    # Ensure the mocked sync was called for both entities
    assert mock_sync.call_count == 1
    mock_sync.assert_any_call(entity_1)

    # Execute command with 2 siret
    mock_sync.reset_mock()
    command.sync_delivery_points([entity_1.siret, entity_2.siret])

    # Ensure the mocked sync was called for both entities
    assert mock_sync.call_count == expected_entities_count
    mock_sync.assert_any_call(entity_1)
    mock_sync.assert_any_call(entity_2)


@pytest.mark.django_db
@patch("apps.core.management.commands.syncdeliverypoints.sync_from_qualicharge_api")
def test_sync_delivery_points_handles_exception(mock_sync_dp):
    """Tests exceptions in `sync_from_qualicharge_api` are handled."""
    assert Entity.objects.all().count() == 0
    EntityFactory()
    assert Entity.objects.all().count() == 1

    # setup sync_entity_from_siret raise an exception
    mock_sync_dp.side_effect = Exception("Sync error")

    with patch("sentry_sdk.capture_exception") as mock_capture_exception:
        # Execute command
        command = Command()
        command.sync_delivery_points()

        # Checks that the mocked method was called, and the exception was caught.
        mock_sync_dp.assert_called_once()
        mock_capture_exception.assert_called_once()


@pytest.mark.django_db
@patch("apps.core.management.commands.syncdeliverypoints.sync_from_qualicharge_api")
def test_sync_delivery_points_no_entities(mock_sync_dp):
    """Tests that the command is not called when there are no entities."""
    assert Entity.objects.all().count() == 0

    # Run the command with no entities
    command = Command()
    command.sync_delivery_points()

    # Check that the func is never called
    mock_sync_dp.assert_not_called()
