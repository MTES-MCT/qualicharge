"""Dashboard core factories."""

import factory
from faker import Faker

from .models import DeliveryPoint, Entity, Station

fake = Faker()


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

    provider_assigned_id = factory.Faker("numerify", text="##############")
    entity = factory.SubFactory(EntityFactory)

    class Meta:  # noqa: D106
        model = DeliveryPoint


class StationFactory(factory.django.DjangoModelFactory):
    """Factory class for creating instances of the Station model."""

    delivery_point = factory.SubFactory(DeliveryPointFactory)
    station_name = factory.Faker("company")

    @factory.lazy_attribute
    def id_station_itinerance(self):
        """Generate a random ID for the station."""
        short_name = fake.bothify(text="???", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        base_id = fake.bothify(
            text=f"FR{short_name}P#####",
        )

        return base_id

    class Meta:  # noqa: D106
        model = Station
