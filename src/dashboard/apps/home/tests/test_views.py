"""Qualicharge: test home.urls."""

from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse

from apps.auth.factories import UserFactory


def test_redirect_for_unauthenticated_user():
    """Test redirect for an unauthenticated user on IndexView."""
    client = Client()
    path = reverse("home:index")
    response = client.get(path)

    assert response.status_code == HTTPStatus.FOUND


@pytest.mark.django_db
def test_index_view_for_authenticated_user(django_user_model):
    """Test the IndexView for an authenticated user."""
    client = Client()
    user = UserFactory()
    client.force_login(user)
    path = reverse("home:index")
    response = client.get(path)

    assert response.status_code == HTTPStatus.OK
