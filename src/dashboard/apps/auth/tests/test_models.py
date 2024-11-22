"""Dashboard auth models tests."""

import pytest

from apps.auth.factories import AdminUserFactory, UserFactory


@pytest.mark.django_db
def test_create_user():
    """Tests the creation of a default user model."""
    user = UserFactory(username="John")

    assert user.username == "John"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_superuser():
    """Tests the creation of a superuser with the user model."""
    admin_user = AdminUserFactory(username="superadmin")

    assert admin_user.username == "superadmin"
    assert admin_user.is_active is True
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
