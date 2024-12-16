"""Dashboard consent dev fixture."""

from apps.auth.factories import UserFactory
from apps.consent import VALIDATED
from apps.consent.factories import ConsentFactory
from apps.core.factories import DeliveryPointFactory, EntityFactory
from apps.core.models import DeliveryPoint


def seed_consent():
    """Creates development fixtures for consent management system.

    This function performs the following tasks:
    1. Creates three user instances using UserFactory.
    2. Creates three entity instances with assigned users using EntityFactory.
    3. Creates multiple delivery points for each entity using DeliveryPointFactory.
    4. Generates consent instances for each delivery point using ConsentFactory.
    """
    # create users
    user1 = UserFactory(username="user1")
    user2 = UserFactory(username="user2")
    user3 = UserFactory(username="user3")
    user4 = UserFactory(username="user4")
    user5 = UserFactory(username="user5")

    # create entities
    entity1 = EntityFactory(users=(user1,))
    entity2 = EntityFactory(users=(user2, user4))
    entity3 = EntityFactory(users=(user3,), proxy_for=(entity1, entity2))
    entity4 = EntityFactory(users=(user5,))

    # create delivery points
    size = 4
    DeliveryPointFactory.create_batch(size, entity=entity1)
    DeliveryPointFactory.create_batch(size, entity=entity2)
    DeliveryPointFactory.create_batch(size, entity=entity3)
    DeliveryPointFactory.create_batch(size, entity=entity4)

    # create past consents with validated status
    for dl in DeliveryPoint.objects.filter(entity=entity1):
        ConsentFactory(delivery_point=dl, created_by=user1, status=VALIDATED)
