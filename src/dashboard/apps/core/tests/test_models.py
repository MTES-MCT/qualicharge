"""Dashboard core models tests."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.core.models import DeliveryPoint, Entity


@pytest.mark.django_db
def test_create_entity():
    """Tests the creation of an entity."""
    User = get_user_model()
    user1 = User.objects.create_user(username="user1", password="foo")  # noqa: S106
    user2 = User.objects.create_user(username="user2", password="foo")  # noqa: S106

    entity = Entity.objects.create(name="abc_entity")
    entity.users.add(user1)
    entity.users.add(user2)
    entity.save()

    # test users have been added.
    assert entity.name == "abc_entity"
    assert all(user in [user1, user2] for user in entity.users.all())

    # test created_at and updated_at have been updated.
    assert entity.created_at is not None
    assert entity.updated_at is not None

    # test IntegrityError: name must not be null
    with pytest.raises(IntegrityError):
        Entity.objects.create(name=None)


@pytest.mark.django_db
def test_update_entity():
    """Tests updating an entity."""
    User = get_user_model()
    user1 = User.objects.create_user(username="user1", password="foo")  # noqa: S106

    entity = Entity.objects.create(name="abc_entity")
    entity.users.add(user1)
    entity.save()

    # test user1 have been removed
    entity.users.remove(user1)
    assert all(user != user1 for user in entity.users.all())

    # test updated_at has been updated
    assert entity.updated_at > entity.created_at


@pytest.mark.django_db
def test_create_delivery_point():
    """Tests the creation of a delivery point."""
    # create users
    User = get_user_model()
    user1 = User.objects.create_user(username="user1", password="foo")  # noqa: S106

    # create entities
    entity1 = Entity.objects.create(name="entity_1")
    entity1.users.add(user1)
    entity1.save()

    entity2 = Entity.objects.create(name="entity_2")
    entity2.users.add(user1)
    entity2.save()

    # create delivery point
    delivery_point = DeliveryPoint.objects.create(provider_id="provider_1234")
    delivery_point.entities.add(entity1)
    delivery_point.entities.add(entity2)
    delivery_point.save()

    assert delivery_point.provider_id == "provider_1234"
    assert delivery_point.is_active is True

    # test entities have been added to delivery point.
    assert all(entity in [entity1, entity2] for entity in delivery_point.entities.all())

    # test created_at and updated_at have been updated.
    assert delivery_point.created_at is not None
    assert delivery_point.updated_at is not None

    # test IntegrityError: provider must not be null
    with pytest.raises(IntegrityError):
        DeliveryPoint.objects.create(provider_id=None)


@pytest.mark.django_db
def test_update_delivery_point():
    """Tests updating a delivery point."""
    # create users
    User = get_user_model()
    user1 = User.objects.create_user(username="user1", password="foo")  # noqa: S106

    # create entity
    entity1 = Entity.objects.create(name="entity_1")
    entity1.users.add(user1)
    entity1.save()

    # create delivery point
    delivery_point = DeliveryPoint.objects.create(provider_id="provider_1234")
    delivery_point.entities.add(entity1)
    delivery_point.save()

    # test entity1 have been removed
    delivery_point.entities.remove(entity1)
    assert all(entity != entity1 for entity in delivery_point.entities.all())

    # test updated_at has been updated
    assert delivery_point.updated_at > delivery_point.created_at
