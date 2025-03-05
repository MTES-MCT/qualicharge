"""Dashboard auth admin tests."""

from http import HTTPStatus

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from apps.auth.admin import DashboardUserAdmin
from apps.auth.factories import AdminUserFactory, UserFactory
from apps.auth.models import DashboardUser
from apps.core.factories import EntityFactory


@pytest.mark.django_db
def test_response_change_sync_entity_success(monkeypatch):
    """Test successful entity synchronization in response_change."""
    entity = EntityFactory()
    fake_siret = "12345678901234"
    fake_user = UserFactory(siret=fake_siret)
    admin_user = AdminUserFactory()

    # mock sync_entity_from_siret()
    monkeypatch.setattr(
        "apps.auth.admin.sync_entity_from_siret", lambda siret, user: entity
    )

    # simulate click on "synchronize entity" button
    site = AdminSite()
    admin = DashboardUserAdmin(DashboardUser, site)
    request = HttpRequest()
    request.method = "POST"
    request.POST["_sync_entity"] = "1"
    request.user = admin_user

    # Add session middleware
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    # mock message handler
    request._messages = FallbackStorage(request)

    # and finally, call the response_change() admin method
    response = admin.response_change(request, fake_user)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == "."

    # check the response message
    messages = list(get_messages(request))
    assert len(messages) == 1
    expected_message = (
        f"Entity with siret {fake_siret} has been synced. "
        f"(Entity: <a href='/admin/qcd_core/entity/{entity.id}/change/' "
        f"target='_blank'>{entity.name}</a>)."
    )
    assert messages[0].message == expected_message
    assert messages[0].level_tag == "success"


@pytest.mark.django_db
def test_response_change_sync_entity_raise_error(monkeypatch):
    """Test error during entity synchronization in response_change."""
    fake_siret = "12345678901234"
    fake_user = UserFactory(siret=fake_siret)
    admin_user = AdminUserFactory()

    # mock sync_entity_from_siret()
    def mock_sync_entity_from_siret(siret, user):
        raise ValidationError("This is a simulated exception.")

    monkeypatch.setattr(
        "apps.auth.admin.sync_entity_from_siret", mock_sync_entity_from_siret
    )

    # simulate click on "synchronize entity" button
    site = AdminSite()
    admin = DashboardUserAdmin(DashboardUser, site)
    request = HttpRequest()
    request.method = "POST"
    request.POST["_sync_entity"] = "1"
    request.user = admin_user

    # Add session middleware
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    # mock message handler
    request._messages = FallbackStorage(request)

    # and finally, call the response_change() admin method
    response = admin.response_change(request, fake_user)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == "."

    # check the error message
    messages = list(get_messages(request))
    assert len(messages) == 1
    expected_message = (
        f"Entity synchronization error ({fake_siret}): "
        f"['This is a simulated exception.']"
    )
    assert messages[0].message == expected_message
    assert messages[0].level_tag == "error"


@pytest.mark.django_db
def test_response_change_no_sync_entity(rf):
    """Test response_change behavior without '_sync_entity' in POST data."""
    fake_user = UserFactory()
    admin_user = AdminUserFactory()

    # simulate standard save (without '_sync_entity')
    site = AdminSite()
    admin = DashboardUserAdmin(DashboardUser, site)
    request = rf.post(f"/admin/qcd_auth/dashboarduser/{fake_user.id}/change/", data={})
    request.user = admin_user

    # Add session middleware
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    # mock message handler
    request._messages = FallbackStorage(request)

    # and finally, call the response_change() admin method
    response = admin.response_change(request, fake_user)

    # Since no '_sync_entity', it should call the parent's response_change
    assert response.status_code == HTTPStatus.FOUND
