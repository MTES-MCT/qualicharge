"""Dashboard core models tests."""

from datetime import datetime, timedelta

import factory
import pytest
from django.db import IntegrityError
from django.utils import timezone
from pytest_django.asserts import assertQuerySetEqual

from apps.auth.factories import UserFactory
from apps.consent import AWAITING, VALIDATED
from apps.consent.factories import ConsentFactory
from apps.consent.models import Consent
from apps.core.factories import DeliveryPointFactory, EntityFactory, StationFactory
from apps.core.models import DeliveryPoint, Entity
from apps.renewable.factories import RenewableFactory
from apps.renewable.models import Renewable


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

    # create upcoming and validated consents for entity2 in futur period (+30 days)
    ConsentFactory(
        delivery_point=dl,
        created_by=user1,
        status=VALIDATED,
        start=timezone.now() + timedelta(days=30),
        end=timezone.now() + timedelta(days=90),
    )

    assert (
        Consent.active_objects.filter(
            status=AWAITING, delivery_point__entity=entity1
        ).count()
        == 4  # noqa: PLR2004
    )
    expected_count = 2
    assert entity1.count_validated_consents() == expected_count
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

    # create awaiting consents for entity1 in past period
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

    # create upcoming and validated consents for entity2 in futur period (+30 days)
    ConsentFactory(
        delivery_point=dl,
        created_by=user1,
        status=VALIDATED,
        start=timezone.now() + timedelta(days=30),
        end=timezone.now() + timedelta(days=90),
    )

    assert (
        Consent.objects.filter(status=AWAITING, delivery_point__entity=entity1).count()
        == 4  # noqa: PLR2004
    )
    assert entity1.count_awaiting_consents() == 3  # noqa: PLR2004
    assert entity2.count_awaiting_consents() == 3  # noqa: PLR2004
    assert entity3.count_awaiting_consents() == 3  # noqa: PLR2004


@pytest.mark.django_db
def test_count_upcoming_consents(settings):
    """Test count_awaiting_consents method."""
    settings.CONSENT_UPCOMING_DAYS_LIMIT = 60
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    entity1 = EntityFactory(users=(user1,), name="entity1")
    entity2 = EntityFactory(users=(user2,), name="entity2")
    entity3 = EntityFactory(
        users=(user3,), proxy_for=(entity1, entity2), name="entity3"
    )

    # create awaiting consent in current period
    for i in range(1, 4):
        DeliveryPointFactory(provider_assigned_id=f"entity1_{i}", entity=entity1)
        DeliveryPointFactory(provider_assigned_id=f"entity2_{i}", entity=entity2)
        DeliveryPointFactory(provider_assigned_id=f"entity3_{i}", entity=entity3)

    # create validated consent for entity1
    dl = DeliveryPointFactory(provider_assigned_id="entity3_validated", entity=entity1)
    Consent.objects.filter(delivery_point=dl).update(status=VALIDATED)

    # create awaiting consents for entity1 in past period
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

    # create upcoming consents for entity1 in futur period (start in 30 days)
    dl = DeliveryPointFactory(provider_assigned_id="entity3_futur30", entity=entity1)
    (
        Consent.objects.filter(
            delivery_point=dl,
            status=AWAITING,
        ).update(
            start=timezone.now() + timedelta(days=29),
            end=timezone.now() + timedelta(days=60),
        )
    )

    # create upcoming consents for entity1 in futur period (start in 90 days)
    dl = DeliveryPointFactory(provider_assigned_id="entity3_futur90", entity=entity1)
    (
        Consent.objects.filter(
            delivery_point=dl,
            status=AWAITING,
        ).update(
            start=timezone.now() + timedelta(days=90),
            end=timezone.now() + timedelta(days=120),
        )
    )

    # create upcoming and validated consents for entity2 in futur period (+30 days)
    ConsentFactory(
        delivery_point=dl,
        created_by=user1,
        status=VALIDATED,
        start=timezone.now() + timedelta(days=30),
        end=timezone.now() + timedelta(days=90),
    )

    assert (
        Consent.objects.filter(status=AWAITING, delivery_point__entity=entity1).count()
        == 6  # noqa: PLR2004
    )
    assert entity1.count_awaiting_consents() == 3  # noqa: PLR2004
    assert entity2.count_awaiting_consents() == 3  # noqa: PLR2004
    assert entity3.count_awaiting_consents() == 3  # noqa: PLR2004
    assert entity1.count_upcoming_consents() == 1


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

    expected_1 = [c1_1, c1_2, c1_3]
    expected_2 = [c2_1, c2_2]
    expected_3 = [c3_1, c3_2]
    assertQuerySetEqual(
        set(entity1.get_consents().order_by("delivery_point")), set(expected_1)
    )
    assertQuerySetEqual(
        set(entity2.get_consents().order_by("delivery_point")), set(expected_2)
    )
    assertQuerySetEqual(
        set(entity3.get_consents().order_by("delivery_point")), set(expected_3)
    )


@pytest.mark.django_db
def test_get_consents_shortcuts(settings):
    """Test get_consents shortcuts method.

    - get_awaiting_consents()
    - get_validated_consents()
    - get_upcoming_consents()
    """
    assert Consent.objects.count() == 0

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

    # get 6 awaiting consents
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

    # upcoming consent limit
    settings.CONSENT_UPCOMING_DAYS_LIMIT = 30

    # create upcoming consents for entity1 in futur period (+30 days)
    c_upcoming_1 = ConsentFactory(
        delivery_point=dl1_1,
        created_by=user1,
        status=AWAITING,
        start=timezone.now() + timedelta(days=30),
        end=timezone.now() + timedelta(days=90),
    )

    # create upcoming consents for entity1 in futur period (+90 days)
    ConsentFactory(
        delivery_point=dl1_2,
        created_by=user1,
        status=AWAITING,
        start=timezone.now() + timedelta(days=90),
        end=timezone.now() + timedelta(days=30),
    )

    # create upcoming and validated consents for entity2 in futur period (+30 days)
    c_upcoming_3 = ConsentFactory(
        delivery_point=dl2_1,
        created_by=user1,
        status=VALIDATED,
        start=timezone.now() + timedelta(days=30),
        end=timezone.now() + timedelta(days=90),
    )

    # count all created consents
    expected_count = 11
    assert Consent.objects.count() == expected_count
    # test with awaiting status
    expected_1 = [c1_1, c1_2]
    expected_2 = [c2_1, c2_2]
    expected_3 = [c3_1, c3_2]
    assertQuerySetEqual(
        set(entity1.get_awaiting_consents().order_by("delivery_point")), set(expected_1)
    )
    assertQuerySetEqual(
        set(entity2.get_awaiting_consents().order_by("delivery_point")), set(expected_2)
    )
    assertQuerySetEqual(
        set(entity3.get_awaiting_consents().order_by("delivery_point")), set(expected_3)
    )

    # test with validated
    assertQuerySetEqual(entity1.get_validated_consents(), [c1_3])
    assertQuerySetEqual(entity2.get_validated_consents(), [c_upcoming_3])
    assertQuerySetEqual(entity3.get_validated_consents(), [])

    # test with upcoming
    assertQuerySetEqual(entity1.get_upcoming_consents(), [c_upcoming_1])
    assertQuerySetEqual(entity2.get_upcoming_consents(), [])
    assertQuerySetEqual(entity3.get_upcoming_consents(), [])


@pytest.mark.django_db
def test_get_linked_stations():
    """Test get_linked_stations return grouped stations by station_name."""
    assert Consent.objects.count() == 0

    # 1 - create entity, delivery points, consents and one station
    entity1 = EntityFactory()
    dp_1 = DeliveryPointFactory(entity=entity1)
    StationFactory(
        delivery_point=dp_1, station_name="Station A", id_station_itinerance="FRABCP01"
    )

    # test stations grouped with a unique station
    result = dp_1.get_linked_stations()
    expected_grouping = {"Station A": ["FRABCP01"]}
    assert result == expected_grouping

    # 2 -create entity, delivery points, consents and many stations
    entity2 = EntityFactory()
    dp_2 = DeliveryPointFactory(entity=entity2)
    StationFactory(
        delivery_point=dp_2, station_name="Station B", id_station_itinerance="FRABCP02"
    )
    StationFactory(
        delivery_point=dp_2, station_name="Station B", id_station_itinerance="FRABCP03"
    )
    StationFactory(
        delivery_point=dp_2, station_name="Station B", id_station_itinerance="FRABCP04"
    )
    StationFactory(
        delivery_point=dp_2, station_name="Station C", id_station_itinerance="FRABCP05"
    )

    # test stations grouped with many stations
    result2 = dp_2.get_linked_stations()
    expected_grouping = {
        "Station B": ["FRABCP02", "FRABCP03", "FRABCP04"],
        "Station C": ["FRABCP05"],
    }
    assert result2 == expected_grouping

    # 3 - create entity, delivery points, consents but without station
    entity3 = EntityFactory()
    dp_3 = DeliveryPointFactory(entity=entity3)

    # test stations grouped without station
    result3 = dp_3.get_linked_stations()
    expected_grouping = {}
    assert result3 == expected_grouping


@pytest.mark.django_db
def test_get_renewables():
    """Test Entity.get_renawables method."""
    INITIAL_SIZE = 4

    # Setup test entities
    entity_with_renewables = EntityFactory()
    entity_without_renewables = EntityFactory()

    # create active delivery points
    dps = DeliveryPointFactory.create_batch(
        INITIAL_SIZE, has_renewable=True, is_active=True, entity=entity_with_renewables
    )

    # create renewables
    assert Renewable.objects.count() == 0
    RenewableFactory.create_batch(
        size=len(dps),
        delivery_point=factory.Iterator(dps),
        collected_at="2024-01-01",
    )
    assert Renewable.objects.count() == INITIAL_SIZE

    # test initial state
    renewables = entity_with_renewables.get_renewables()
    assert renewables.count() == INITIAL_SIZE
    for r in renewables:
        assert r.delivery_point.has_renewable is True
        assert r.delivery_point.is_active is True

    # test entity without renewables
    renewables = entity_without_renewables.get_renewables()
    assert renewables.count() == 0

    # Test with non-renewable delivery point
    dps[0].has_renewable = False
    dps[0].save()
    renewables = entity_with_renewables.get_renewables()
    expected_size = 3
    assert renewables.count() == expected_size
    assert all(r.delivery_point.id != dps[0].id for r in renewables)

    # Test with inactive delivery point
    dps[1].is_active = False
    dps[1].save()
    renewables = entity_with_renewables.get_renewables()
    expected_size = 2
    assert renewables.count() == expected_size
    assert all(r.delivery_point.id not in [dps[0].id, dps[1].id] for r in renewables)


@pytest.mark.django_db
def test_get_unsubmitted_quarterly_renewables(monkeypatch):
    """Test Entity.get_unsubmitted_quarterly_renewables method."""
    INITIAL_SIZE = 4
    mock_now = datetime(2025, 3, 6)
    monkeypatch.setattr(timezone, "now", lambda: mock_now)

    # Setup test entities
    entity_with_renewables = EntityFactory()
    entity_without_renewables = EntityFactory()

    # create active delivery points
    dps = DeliveryPointFactory.create_batch(
        INITIAL_SIZE, has_renewable=True, is_active=True, entity=entity_with_renewables
    )

    assert Renewable.objects.count() == 0
    # Create a previous renewable to test `last_renewable.meter_reading`
    # and `last_renewable.collected_at`
    previous_date = "2024-09-20"
    previous_meter_reading = 1000.5
    RenewableFactory(
        delivery_point=dps[1],
        collected_at=previous_date,
        meter_reading=previous_meter_reading,
    )
    # create older renewables for all delivery points
    RenewableFactory.create_batch(
        size=len(dps),
        delivery_point=factory.Iterator(dps),
        collected_at="2023-01-01",
    )
    # create submitted renewable for the testing quarter (so, the previous from now)
    submitted_renewable = RenewableFactory(
        delivery_point=dps[0],
        collected_at="2024-12-21",
    )
    expected_size = 6
    assert Renewable.objects.count() == expected_size

    # test entity without renewables
    renewable_dps = entity_without_renewables.get_unsubmitted_quarterly_renewables()
    assert renewable_dps.count() == 0

    # test entity with renewables
    renewable_dps = entity_with_renewables.get_unsubmitted_quarterly_renewables()
    expected_size = 3
    assert renewable_dps.count() == expected_size
    assert all(r.id != submitted_renewable.id for r in renewable_dps)

    # test the `last_renewable.meter_reading` and `last_renewable.collected_at` fields
    first_dp = renewable_dps.get(id=dps[1].id)
    assert first_dp.last_renewable[0].meter_reading == previous_meter_reading
    assert first_dp.last_renewable[0].collected_at.strftime("%Y-%m-%d") == previous_date


@pytest.mark.django_db
def test_count_renewables():
    """Test Entity.count_renawables method."""
    INITIAL_SIZE = 4

    # Setup test entities
    entity_with_renewables = EntityFactory()
    entity_without_renewables = EntityFactory()

    # create active delivery points
    dps = DeliveryPointFactory.create_batch(
        INITIAL_SIZE, has_renewable=True, is_active=True, entity=entity_with_renewables
    )

    # create renewables
    assert Renewable.objects.count() == 0
    RenewableFactory.create_batch(
        size=len(dps),
        delivery_point=factory.Iterator(dps),
        collected_at="2024-01-01",
    )
    assert Renewable.objects.count() == INITIAL_SIZE

    # test initial state
    assert entity_with_renewables.count_renewables() == INITIAL_SIZE

    # test entity without renewables
    assert entity_without_renewables.count_renewables() == 0

    # Test with non-renewable delivery point
    dps[0].has_renewable = False
    dps[0].save()
    expected_size = 3
    assert entity_with_renewables.count_renewables() == expected_size

    # Test with inactive delivery point
    dps[1].is_active = False
    dps[1].save()
    expected_size = 2
    assert entity_with_renewables.count_renewables() == expected_size


@pytest.mark.django_db
def test_count_unsubmitted_quarterly_renewables(monkeypatch):
    """Test Entity.count_unsubmitted_quarterly_renewables method."""
    INITIAL_SIZE = 4
    mock_now = datetime(2025, 3, 6)
    monkeypatch.setattr(timezone, "now", lambda: mock_now)

    # Setup test entities
    entity_with_renewables = EntityFactory()
    entity_without_renewables = EntityFactory()

    # create active delivery points
    dps = DeliveryPointFactory.create_batch(
        INITIAL_SIZE, has_renewable=True, is_active=True, entity=entity_with_renewables
    )

    # create old renewables
    assert Renewable.objects.count() == 0
    RenewableFactory.create_batch(
        size=len(dps),
        delivery_point=factory.Iterator(dps),
        collected_at="2024-01-01",
    )
    # create renewables for the current quarter
    RenewableFactory(
        delivery_point=dps[0],
        collected_at="2024-12-21",
    )
    expected_size = 5
    assert Renewable.objects.count() == expected_size

    # test entity without renewables
    assert entity_without_renewables.count_unsubmitted_quarterly_renewables() == 0

    # test entity with renewables
    expected_size = 3
    assert (
        entity_with_renewables.count_unsubmitted_quarterly_renewables() == expected_size
    )


@pytest.mark.django_db
def test_entity_has_renewable():
    """Test Entity.has_renewable method."""
    # create, users, entity and consents
    entity = EntityFactory()
    DeliveryPointFactory(has_renewable=True, is_active=True, entity=entity)
    assert entity.has_renewable() is True

    entity_without_renewable = EntityFactory()
    DeliveryPointFactory(has_renewable=False, is_active=True, entity=entity)
    assert entity_without_renewable.has_renewable() is False


@pytest.mark.django_db
def test_entity_count_active_delivery_points():
    """Test Entity.count_active_delivery_points method."""
    entity = EntityFactory()
    assert entity._count_active_delivery_points is None

    active_dp_size = 3
    inactive_dp_size = 2
    expected_size = 5
    DeliveryPointFactory.create_batch(
        size=active_dp_size, entity=entity, is_active=True
    )
    DeliveryPointFactory.create_batch(
        size=inactive_dp_size, entity=entity, is_active=False
    )

    # test the initial count of active delivery points
    assert DeliveryPoint.objects.count() == expected_size
    count = entity.count_active_delivery_points()
    assert entity._count_active_delivery_points is not None
    assert count == active_dp_size

    # test the value is cached
    DeliveryPointFactory(entity=entity, is_active=True)
    cached_active_dp_size = 3
    expected_size = 6
    assert DeliveryPoint.objects.count() == expected_size
    cached_count = entity.count_active_delivery_points()
    assert cached_count == cached_active_dp_size

    # test the forced count update
    updated_active_dp_size = 4
    updated_count = entity.count_active_delivery_points(update=True)
    assert updated_count == updated_active_dp_size

    # test the status change of a delivery point.
    dp = DeliveryPoint.objects.filter(is_active=True).first()
    dp.is_active = False
    dp.save()
    new_count = entity.count_active_delivery_points(update=True)
    expected_new_count = 3
    assert new_count == expected_new_count
