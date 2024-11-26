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

    entity2 = EntityFactory(name="entity 2", users=(user1, user2))
    entity3 = EntityFactory(name="entity 3", users=(user1, user2))
    entity = EntityFactory(
        name="entity 1", users=(user1, user2), proxy_for=(entity2, entity3)
    )

    assert entity.name == "entity 1"
    assert entity.slug == "entity-1"

    # test users have been added.
    assert all(user in entity.users.all() for user in [user1, user2])

    # test `proxy_for` have been added.
    assert all(proxy_for in entity.proxy_for.all() for proxy_for in [entity2, entity3])

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
    entity2 = EntityFactory(name="entity 2")
    entity = EntityFactory(users=(user1,), proxy_for=(entity2,))

    # test user1 have been removed
    entity.users.remove(user1)
    assert all(user != user1 for user in entity.users.all())

    # test `proxy_for` have been removed
    entity.proxy_for.remove(entity2)
    assert all(entity != entity2 for entity in entity.proxy_for.all())

    # test updated_at has been updated
    assert entity.updated_at > entity.created_at


@pytest.mark.django_db
def test_create_delivery_point():
    """Tests the creation of a delivery point."""
    # create users
    user1 = UserFactory()

    # create entities
    entity1 = EntityFactory(users=(user1,))

    # create delivery point
    delivery_point = DeliveryPointFactory(
        provider_assigned_id="dp_1234", entity=entity1
    )

    assert delivery_point.provider_assigned_id == "dp_1234"
    assert delivery_point.is_active is True
    assert delivery_point.entity == entity1

    # test created_at and updated_at have been updated.
    assert delivery_point.created_at is not None
    assert delivery_point.updated_at is not None


@pytest.mark.django_db
def test_integrity_error_create_provider_assigned_id_null():
    """Test IntegrityError on provider_assigned_id.

    provider_assigned_id must not be null.
    """
    with pytest.raises(IntegrityError):
        DeliveryPointFactory(provider_assigned_id=None)


@pytest.mark.django_db
def test_integrity_error_create_entity_null():
    """Test IntegrityError on entity.

    Entity fk must not be null.
    """
    with pytest.raises(IntegrityError):
        DeliveryPointFactory(provider_assigned_id="dp1", entity=None)


@pytest.mark.django_db
def test_update_delivery_point():
    """Tests updating a delivery point."""
    # create users
    user1 = UserFactory()

    # create entity
    entity1 = EntityFactory(users=(user1,))

    # create delivery point
    delivery_point = DeliveryPointFactory(entity=entity1)

    # test updated_at has been updated
    assert delivery_point.updated_at > delivery_point.created_at
