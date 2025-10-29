"""Qualicharge: test home.urls."""

import datetime
from http import HTTPStatus

import pytest
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.auth.factories import UserFactory


def test_redirect_for_unauthenticated_user(client):
    """Test redirect for an unauthenticated user on IndexView."""
    client = Client()

    path = reverse("home:index")
    response = client.get(path)

    # the user should be redirected to the login page
    assert response.status_code == HTTPStatus.FOUND
    assert "login" in response.url


@pytest.mark.django_db
def test_index_view_for_authenticated_user(client):
    """Test the IndexView for an authenticated user."""
    user = UserFactory()
    client.force_login(user)

    path = reverse("home:index")
    response = client.get(path)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_session_expiration(client):
    """Test that the session expires after SESSION_COOKIE_AGE seconds."""
    user = UserFactory()
    client.force_login(user)

    path = reverse("home:index")
    response = client.get(path)

    # user should be logged in
    assert response.status_code == HTTPStatus.OK

    # we retrieve the current session…
    session_key = client.session.session_key
    session = Session.objects.get(session_key=session_key)

    # … and simulate expiration (by shifting the expiration into the past)
    session.expire_date = timezone.now() - datetime.timedelta(seconds=1)
    session.save()

    # New request: the user should be redirected to the login page
    response = client.get(path)
    assert response.status_code == HTTPStatus.FOUND  # redirigé vers la page de login
    assert "login" in response.url
