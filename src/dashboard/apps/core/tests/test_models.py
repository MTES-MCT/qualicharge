"""Dashboard core models tests."""

import pytest
from django.db import IntegrityError

from apps.auth.factories import UserFactory
from apps.core.factories import DeliveryPointFactory, EntityFactory
from apps.core.models import Entity


@pytest.mark.django_db
def test_create_entity():
    """Tests the creation of an entity."""
    user1 = UserFactory()
    user2 = UserFactory()

    entity = EntityFactory(name="entity_1234", users=(user1, user2))

    # test users have been added.
    assert entity.name == "entity_1234"
    assert all(user in entity.users.all() for user in [user1, user2])

    # test created_at and updated_at have been updated.
    assert entity.created_at is not None
    assert entity.updated_at is not None

    # test IntegrityError: name must not be null
    with pytest.raises(IntegrityError):
        Entity.objects.create(name=None)


@pytest.mark.django_db
def test_update_entity():
    """Tests updating an entity."""
    user1 = UserFactory()
    entity = EntityFactory(users=(user1,))

    # test user1 have been removed
    entity.users.remove(user1)
    assert all(user != user1 for user in entity.users.all())

    # test updated_at has been updated
    assert entity.updated_at > entity.created_at


@pytest.mark.django_db
def test_create_delivery_point():
    """Tests the creation of a delivery point."""
    # create users
    user1 = UserFactory()

    # create entities
    entity1 = EntityFactory(users=(user1,))
    entity2 = EntityFactory(users=(user1,))

    # create delivery point
    delivery_point = DeliveryPointFactory(
        provider_id="provider_1234", entities=(entity1, entity2)
    )

    assert delivery_point.provider_id == "provider_1234"
    assert delivery_point.is_active is True

    # test entities have been added to delivery point.
    assert all(entity in delivery_point.entities.all() for entity in [entity1, entity2])

    # test created_at and updated_at have been updated.
    assert delivery_point.created_at is not None
    assert delivery_point.updated_at is not None

    # test IntegrityError: provider must not be null
    with pytest.raises(IntegrityError):
        DeliveryPointFactory(provider_id=None)


@pytest.mark.django_db
def test_update_delivery_point():
    """Tests updating a delivery point."""
    # create users
    user1 = UserFactory()

    # create entity
    entity1 = EntityFactory(users=(user1,))

    # create delivery point
    delivery_point = DeliveryPointFactory(entities=(entity1,))

    # test entity1 have been removed
    delivery_point.entities.remove(entity1)
    assert all(entity != entity1 for entity in delivery_point.entities.all())

    # test updated_at has been updated
    assert delivery_point.updated_at > delivery_point.created_at
