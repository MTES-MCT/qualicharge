"""Dashboard auth models tests."""

import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_create_user():
    """Tests the creation of a default user model."""
    User = get_user_model()
    user = User.objects.create_user(username="john", password="foo")  # noqa: S106

    assert user.username == "john"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_superuser():
    """Tests the creation of a superuser with the user model."""
    User = get_user_model()
    admin_user = User.objects.create_superuser(
        username="superadmin", password="foo"  # noqa: S106
    )

    assert admin_user.username == "superadmin"
    assert admin_user.is_active is True
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
