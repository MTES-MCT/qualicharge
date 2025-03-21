"""Dashboard core factories."""

import random

import factory

from .models import DeliveryPoint, Entity


class EntityFactory(factory.django.DjangoModelFactory):
    """Factory class for creating instances of the Entity model."""

    name = factory.Faker("company")
    legal_form = factory.Faker(
        "random_element", elements=["SA", "SARL", "SAS", "SCOP", "EI"]
    )
    trade_name = factory.Faker("company")
    siret = factory.Faker("numerify", text="##############")
    naf = factory.Faker("bothify", text="####?", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    address_1 = factory.Faker("street_address")
    address_2 = factory.Faker("secondary_address")
    address_zip_code = factory.Faker("postcode")
    address_city = factory.Faker("city")

    class Meta:  # noqa: D106
        model = Entity
        skip_postgeneration_save = True

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

    id_station_itinerance = factory.Faker(
        "bothify", text="FR???P#####", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    station_name = factory.Faker("company")
    provider_assigned_id = factory.LazyAttribute(
        lambda o: f"{o.id_station_itinerance}{random.randint(0, 9)}"  # noqa: S311
    )
    entity = factory.SubFactory(EntityFactory)

    class Meta:  # noqa: D106
        model = DeliveryPoint
