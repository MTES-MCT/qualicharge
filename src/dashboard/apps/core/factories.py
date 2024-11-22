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


class DeliveryPointFactory(factory.django.DjangoModelFactory):
    """Factory class for creating instances of the DeliveryPoint model."""

    class Meta:  # noqa: D106
        model = DeliveryPoint

    provider_id = factory.Sequence(lambda n: "provider_%d" % n)

    @factory.post_generation
    def entities(self, create, extracted, **kwargs):
        """Method to add entities after the delivery point is created."""
        if not create or not extracted:
            # Simple build, or nothing to add, do nothing.
            return

        # Add the iterable of groups using bulk addition
        self.entities.add(*extracted)
