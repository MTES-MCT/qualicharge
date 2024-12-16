"""Dashboard core models tests."""

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone
from pytest_django.asserts import assertQuerySetEqual

from apps.auth.factories import UserFactory
from apps.consent import AWAITING, VALIDATED
from apps.consent.factories import ConsentFactory
from apps.consent.models import Consent
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


@pytest.mark.django_db
def test_is_proxy_for():
    """Test is_proxy_for method."""
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    entity1 = EntityFactory(users=(user1,), name="entity1")
    entity2 = EntityFactory(users=(user2,), name="entity2")
    entity3 = EntityFactory(
        users=(user3,), proxy_for=(entity1, entity2), name="entity3"
    )
    assert entity1.is_proxy_for() is False
    assert entity3.is_proxy_for() is True


@pytest.mark.django_db
def test_get_proxy_entities_list():
    """Test get_proxy_entities_list method."""
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    entity1 = EntityFactory(users=(user1,), name="entity1")
    entity2 = EntityFactory(users=(user2,), name="entity2")
    entity3 = EntityFactory(
        users=(user3,), proxy_for=(entity1, entity2), name="entity3"
    )
    # entity1 is not a proxy_for
    assertQuerySetEqual(entity1.get_proxy_entities(), [])

    # entity3 is proxy_for entity1 and entity2
    assertQuerySetEqual(entity3.get_proxy_entities(), [entity1, entity2])


@pytest.mark.django_db
def test_count_validated_consents():
    """Test count_validated_consents method."""
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    entity1 = EntityFactory(users=(user1,), name="entity1")
    entity2 = EntityFactory(users=(user2,), name="entity2")
    entity3 = EntityFactory(
        users=(user3,), proxy_for=(entity1, entity2), name="entity3"
    )

    for i in range(1, 4):
        DeliveryPointFactory(provider_assigned_id=f"entity1_{i}", entity=entity1)
        DeliveryPointFactory(provider_assigned_id=f"entity2_{i}", entity=entity2)
        DeliveryPointFactory(provider_assigned_id=f"entity3_{i}", entity=entity3)

    # create validated consent for entity1
    dl = DeliveryPointFactory(provider_assigned_id="entity3_validated", entity=entity1)
    ConsentFactory(delivery_point=dl, status=VALIDATED)

    # create awaiting consents for entity1 in past period
    ConsentFactory(
        delivery_point=dl,
        status=AWAITING,
        start=timezone.now() - timedelta(days=300),
        end=timezone.now() - timedelta(days=270),
    )

    assert (
        Consent.active_objects.filter(
            status=AWAITING, delivery_point__entity=entity1
        ).count()
        == 4  # noqa: PLR2004
    )
    assert entity1.count_validated_consents() == 1
    assert entity2.count_validated_consents() == 0
    assert entity3.count_validated_consents() == 0


@pytest.mark.django_db
def test_count_awaiting_consents():
    """Test count_awaiting_consents method."""
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    entity1 = EntityFactory(users=(user1,), name="entity1")
    entity2 = EntityFactory(users=(user2,), name="entity2")
    entity3 = EntityFactory(
        users=(user3,), proxy_for=(entity1, entity2), name="entity3"
    )

    for i in range(1, 4):
        DeliveryPointFactory(provider_assigned_id=f"entity1_{i}", entity=entity1)
        DeliveryPointFactory(provider_assigned_id=f"entity2_{i}", entity=entity2)
        DeliveryPointFactory(provider_assigned_id=f"entity3_{i}", entity=entity3)

    # create validated consent for entity1
    dl = DeliveryPointFactory(provider_assigned_id="entity3_validated", entity=entity1)
    Consent.objects.filter(delivery_point=dl).update(status=VALIDATED)

    # create awainting consents for entity1 in past period
    dl = DeliveryPointFactory(provider_assigned_id="entity3_past", entity=entity1)
    (
        Consent.objects.filter(
            delivery_point=dl,
            status=AWAITING,
        ).update(
            start=timezone.now() - timedelta(days=300),
            end=timezone.now() - timedelta(days=270),
        )
    )

    assert (
        Consent.objects.filter(status=AWAITING, delivery_point__entity=entity1).count()
        == 4  # noqa: PLR2004
    )
    assert entity1.count_awaiting_consents() == 3  # noqa: PLR2004
    assert entity2.count_awaiting_consents() == 3  # noqa: PLR2004
    assert entity3.count_awaiting_consents() == 3  # noqa: PLR2004


@pytest.mark.django_db
def test_get_consents():
    """Test get_consents method."""
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    entity1 = EntityFactory(users=(user1,), name="entity1")
    entity2 = EntityFactory(users=(user2,), name="entity2")
    entity3 = EntityFactory(
        users=(user3,), proxy_for=(entity1, entity2), name="entity3"
    )

    # create delivery points
    dl1_1 = DeliveryPointFactory(provider_assigned_id="entity1_1", entity=entity1)
    dl1_2 = DeliveryPointFactory(provider_assigned_id="entity1_2", entity=entity1)
    dl1_3 = DeliveryPointFactory(provider_assigned_id="entity1_3", entity=entity1)
    dl2_1 = DeliveryPointFactory(provider_assigned_id="entity2_1", entity=entity2)
    dl2_2 = DeliveryPointFactory(provider_assigned_id="entity2_2", entity=entity2)
    dl3_1 = DeliveryPointFactory(provider_assigned_id="entity3_1", entity=entity3)
    dl3_2 = DeliveryPointFactory(provider_assigned_id="entity3_2", entity=entity3)

    # get awaiting consents
    c1_1 = Consent.objects.get(delivery_point=dl1_1, status=AWAITING)
    c1_2 = Consent.objects.get(delivery_point=dl1_2, status=AWAITING)
    c2_1 = Consent.objects.get(delivery_point=dl2_1, status=AWAITING)
    c2_2 = Consent.objects.get(delivery_point=dl2_2, status=AWAITING)
    c3_1 = Consent.objects.get(delivery_point=dl3_1, status=AWAITING)
    c3_2 = Consent.objects.get(delivery_point=dl3_2, status=AWAITING)

    # update consent c1_3 to validated
    c1_3 = Consent.objects.get(delivery_point=dl1_3)
    c1_3.status = VALIDATED
    c1_3.save()

    # create awaiting consents for entity1 in past period
    ConsentFactory(
        delivery_point=dl1_1,
        created_by=user1,
        status=AWAITING,
        start=timezone.now() - timedelta(days=300),
        end=timezone.now() - timedelta(days=270),
    )

    assertQuerySetEqual(
        entity1.get_consents().order_by("delivery_point"), [c1_1, c1_2, c1_3]
    )
    assertQuerySetEqual(entity2.get_consents(), [c2_1, c2_2])
    assertQuerySetEqual(entity3.get_consents(), [c3_1, c3_2])


@pytest.mark.django_db
def test_get_awaiting_consents():
    """Test get_awaiting_consents method."""
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    entity1 = EntityFactory(users=(user1,), name="entity1")
    entity2 = EntityFactory(users=(user2,), name="entity2")
    entity3 = EntityFactory(
        users=(user3,), proxy_for=(entity1, entity2), name="entity3"
    )

    # create delivery points
    dl1_1 = DeliveryPointFactory(provider_assigned_id="entity1_1", entity=entity1)
    dl1_2 = DeliveryPointFactory(provider_assigned_id="entity1_2", entity=entity1)
    dl1_3 = DeliveryPointFactory(provider_assigned_id="entity1_3", entity=entity1)
    dl2_1 = DeliveryPointFactory(provider_assigned_id="entity2_1", entity=entity2)
    dl2_2 = DeliveryPointFactory(provider_assigned_id="entity2_2", entity=entity2)
    dl3_1 = DeliveryPointFactory(provider_assigned_id="entity3_1", entity=entity3)
    dl3_2 = DeliveryPointFactory(provider_assigned_id="entity3_2", entity=entity3)

    # get awaiting consents
    c1_1 = Consent.objects.get(delivery_point=dl1_1, status=AWAITING)
    c1_2 = Consent.objects.get(delivery_point=dl1_2, status=AWAITING)
    c2_1 = Consent.objects.get(delivery_point=dl2_1, status=AWAITING)
    c2_2 = Consent.objects.get(delivery_point=dl2_2, status=AWAITING)
    c3_1 = Consent.objects.get(delivery_point=dl3_1, status=AWAITING)
    c3_2 = Consent.objects.get(delivery_point=dl3_2, status=AWAITING)

    # update consent c1_3 to validated
    c1_3 = Consent.objects.get(delivery_point=dl1_3)
    c1_3.status = VALIDATED
    c1_3.save()

    # create awaiting consents for entity1 in past period
    ConsentFactory(
        delivery_point=dl1_1,
        created_by=user1,
        status=AWAITING,
        start=timezone.now() - timedelta(days=300),
        end=timezone.now() - timedelta(days=270),
    )

    # test with awaiting status
    assertQuerySetEqual(entity1.get_awaiting_consents(), [c1_1, c1_2])
    assertQuerySetEqual(entity2.get_awaiting_consents(), [c2_1, c2_2])
    assertQuerySetEqual(entity3.get_awaiting_consents(), [c3_1, c3_2])
