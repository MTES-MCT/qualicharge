"""Dashboard core mixins tests."""

import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from apps.auth.factories import UserFactory
from apps.core.factories import EntityFactory
from apps.core.mixins import EntityViewMixin


@pytest.mark.django_db
def test_get_entity_success(rf):
    """Test get_entity returns the correct entity when permissions are valid."""
    user = UserFactory()
    entity = EntityFactory(name="Test Entity", users=[user])
    request = rf.get("/some-path/")
    request.user = user

    mixin = EntityViewMixin()
    mixin.request = request
    mixin.kwargs = {"slug": "test-entity"}

    retrieved_entity = mixin.get_entity()
    assert retrieved_entity == entity


@pytest.mark.django_db
def test_get_entity_missing_slug(rf):
    """Test get_entity raises Http404 when slug is missing."""
    user = UserFactory()
    request = rf.get("/some-path/")
    request.user = user

    mixin = EntityViewMixin()
    mixin.request = request
    mixin.kwargs = {}

    with pytest.raises(Http404):
        mixin.get_entity()


@pytest.mark.django_db
def test_get_entity_invalid_slug(rf):
    """Test get_entity raises 404 when entity with the provided slug doesn't exist."""
    user = UserFactory()
    request = rf.get("/some-path/")
    request.user = user

    mixin = EntityViewMixin()
    mixin.request = request
    mixin.kwargs = {"slug": "non-existent-slug"}

    with pytest.raises(Http404):
        mixin.get_entity()


@pytest.mark.django_db
def test_get_entity_permission_denied(rf):
    """Test get_entity raises PermissionDenied when the user lacks permissions."""
    user = UserFactory()
    EntityFactory(name="Test Entity")
    request = rf.get("/some-path/")
    request.user = user

    mixin = EntityViewMixin()
    mixin.request = request
    mixin.kwargs = {"slug": "test-entity"}

    with pytest.raises(PermissionDenied):
        mixin.get_entity()
