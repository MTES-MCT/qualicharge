"""Dashboard auth factories."""

import factory
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    """Factory class for creating a “standard” user."""

    username = factory.Faker("user_name")
    password = factory.django.Password("foo")
    is_validated = True

    class Meta:  # noqa: D106
        model = get_user_model()


class AdminUserFactory(UserFactory):
    """Factory class for creating a superuser."""

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with ``create_superuser``."""
        manager = cls._get_manager(model_class)
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create_superuser(*args, **kwargs)
