"""Dashboard auth models tests."""

from unittest.mock import patch

import pytest
from pytest_django.asserts import assertQuerySetEqual

from apps.auth.factories import AdminUserFactory, UserFactory
from apps.core.factories import EntityFactory


@pytest.mark.django_db
def test_create_user():
    """Tests the creation of a default user model."""
    user = UserFactory(username="John")

    assert user.username == "John"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_superuser():
    """Tests the creation of a superuser with the user model."""
    admin_user = AdminUserFactory(username="superadmin")

    assert admin_user.username == "superadmin"
    assert admin_user.is_active is True
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True


@pytest.mark.django_db
def test_get_entities():
    """Test that user retrieve his entities."""
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    entity1 = EntityFactory(users=(user1,), name="entity1")
    entity2 = EntityFactory(users=(user2,), name="entity2")
    entity3 = EntityFactory(
        users=(user3,), proxy_for=(entity1, entity2), name="entity3"
    )

    assertQuerySetEqual(user1.get_entities(), [entity1])
    assertQuerySetEqual(user2.get_entities(), [entity2])

    user1_entities = user3.get_entities()
    user1_expected_entities = [entity1, entity2, entity3]
    assertQuerySetEqual(user1_entities, user1_expected_entities)


@pytest.mark.django_db
def test_can_validate_entity():
    """Test if user can validate an entity."""
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    user4 = UserFactory()

    entity1 = EntityFactory(users=(user1,), name="entity1")
    entity2 = EntityFactory(users=(user2,), name="entity2")
    entity3 = EntityFactory(
        users=(user3,), proxy_for=(entity1, entity2), name="entity3"
    )
    # multiple entities including one with proxy_for
    entity4 = EntityFactory(users=(user4,), name="entity4")
    entity5 = EntityFactory(users=(user4,), proxy_for=(entity2,), name="entity5")

    assert user1.can_validate_entity(entity1) is True
    assert user1.can_validate_entity(entity2) is False
    assert user1.can_validate_entity(entity3) is False

    assert user3.can_validate_entity(entity1) is True
    assert user3.can_validate_entity(entity2) is True
    assert user3.can_validate_entity(entity3) is True
    assert user3.can_validate_entity(entity4) is False

    assert user4.can_validate_entity(entity4) is True
    assert user4.can_validate_entity(entity5) is True
    assert user4.can_validate_entity(entity2) is True


@pytest.mark.django_db
def test_save_triggers_validation_email():
    """Test the `save` method triggers a validation email."""
    user = UserFactory(is_validated=False)

    # `is_validated` doesn't change to True: an email should NOT be sent.
    with patch("apps.auth.models.send_validation_email") as mock_send_email:
        user.save()
        assert user.is_validated is False
        mock_send_email.assert_not_called()

    # `is_validated` changes to True: an email should be sent.
    with patch("apps.auth.models.send_validation_email") as mock_send_email:
        user.refresh_from_db()
        assert user.is_validated is False
        user.is_validated = True
        user.save()
        assert user.is_validated is True
        mock_send_email.assert_called_once_with(user)

    # `is_validated` remains to True: an email should NOT be sent.
    with patch("apps.auth.models.send_validation_email") as mock_send_email:
        user.refresh_from_db()
        assert user.is_validated is True
        user.is_validated = True
        user.save()
        assert user.is_validated is True
        mock_send_email.assert_not_called()
