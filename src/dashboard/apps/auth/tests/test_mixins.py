"""Dashboard auth mixins tests."""

from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.http import HttpResponse
from django.views import View

from apps.auth.factories import UserFactory
from apps.auth.mixins import UserValidationMixin


class MockView(UserValidationMixin, View):
    """Mock view to test the UserValidationMixin."""

    def get(self, request, *args, **kwargs):
        """Mock get method."""
        return HttpResponse("View response")


@pytest.mark.django_db
def test_user_not_validated_renders_not_validated_template(rf):
    """Test that a user not validated renders the 'not validated' template."""
    user = UserFactory(is_validated=False)

    request = rf.get("/")
    request.user = user

    view = MockView()
    with patch("apps.auth.mixins.redirect") as mock_redirect:
        view.dispatch(request)
        mock_redirect.assert_called_once_with("qcd_auth:not_validated")


@pytest.mark.django_db
def test_validated_user_renders_parent_view(rf):
    """Test that a validated user renders the parent view."""
    user = UserFactory(is_validated=True)

    request = rf.get("/")
    request.user = user

    view = MockView()
    response = view.dispatch(request)

    assert response.status_code == HTTPStatus.OK
    assert response.content == b"View response"
