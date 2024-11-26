"""Dashboard core factories."""

import factory

from .models import DeliveryPoint, Entity


class EntityFactory(factory.django.DjangoModelFactory):
    """Factory class for creating instances of the Entity model."""

    name = factory.Faker("company")

    class Meta:  # noqa: D106
        model = Entity

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        """Method to add users after the entity is created."""
        if not create or not extracted:
            # Simple build, or nothing to add, do nothing.
            return

        # Add the iterable of groups using bulk addition
        self.users.add(*extracted)

    @factory.post_generation
    def proxy_for(self, create, extracted, **kwargs):
        """Method to add `proxy_for` after the entity is created."""
        if not create or not extracted:
            # Simple build, or nothing to add, do nothing.
            return

        self.proxy_for.add(*extracted)


class DeliveryPointFactory(factory.django.DjangoModelFactory):
    """Factory class for creating instances of the DeliveryPoint model."""

    class Meta:  # noqa: D106
        model = DeliveryPoint

    provider_assigned_id = factory.Sequence(lambda n: "dp_%d" % n)
    entity = factory.SubFactory(EntityFactory)
