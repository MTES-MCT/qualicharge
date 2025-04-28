"""Dashboard renewable views tests."""

from http import HTTPStatus

import pytest
from django.urls import reverse

from apps.auth.factories import UserFactory
from apps.auth.mixins import UserValidationMixin
from apps.core.factories import DeliveryPointFactory, EntityFactory
from apps.core.mixins import EntityMixin
from apps.core.models import DeliveryPoint
from apps.renewable.views import RenewableMetterReadingFormView


@pytest.mark.django_db
def test_view_inherits_entity_mixin():
    """Test RenewableMetterReadingFormView inherits mixins."""
    assert issubclass(RenewableMetterReadingFormView, EntityMixin)
    assert issubclass(RenewableMetterReadingFormView, UserValidationMixin)


@pytest.mark.django_db
def test_manage_views_with_not_logged_user_is_restricted(client):
    """Test access to renewable:manage with not logged is restricted."""
    entity_name = "entity-1"
    EntityFactory(name=entity_name)

    url = reverse("renewable:manage", kwargs={"slug": entity_name})
    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_manage_views_without_slug_is_redirected(client):
    """Test direct access to renewable:manage is redirected to index."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("renewable:manage"))
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("renewable:index")


@pytest.mark.django_db
def test_manage_views_with_wrong_slug_raised_404(client):
    """Test direct access to renewable:manage is redirected to index."""
    user = UserFactory()
    client.force_login(user)

    entity_name = "entity-1"
    wrong_slug = "wrong-slug"
    EntityFactory(name=entity_name, users=[user])

    url = reverse("renewable:manage", kwargs={"slug": wrong_slug})
    response = client.get(url)

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_manage_views_rendered_without_data(client):
    """Test manage view without data."""
    user = UserFactory()
    client.force_login(user)

    entity_name = "entity-1"
    EntityFactory(name=entity_name, users=[user])
    url = reverse("renewable:manage", kwargs={"slug": entity_name})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    # force template rendering
    rendered = response.render()
    html = rendered.content.decode()

    expected_html_id = 'id="no-data-card"'
    assert (expected_html_id in html) is True


@pytest.mark.django_db
def test_manage_views_rendered_with_data(client):
    """Test manage view without data."""
    user = UserFactory()
    client.force_login(user)

    # create entity and associated delivery points
    assert DeliveryPoint.objects.all().count() == 0
    entity_name = "entity-1"
    entity = EntityFactory(name=entity_name, users=[user])
    size = 4
    dps = DeliveryPointFactory.create_batch(
        size=size,
        entity=entity,
        has_renewable=True,
        is_active=True,
    )
    assert DeliveryPoint.objects.all().count() == size

    # render manage view
    url = reverse("renewable:manage", kwargs={"slug": entity_name})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    # force template rendering
    rendered = response.render()
    html = rendered.content.decode()

    # test all delivery points are listed
    assert all(str(dp.provider_assigned_id) in html for dp in dps)


@pytest.mark.django_db
def test_manage_views_get_context_data(rf, settings):
    """Test get_context_data() method of RenewableMetterReadingFormView."""
    expected_signature_location = "signature location"
    settings.CONSENT_SIGNATURE_LOCATION = expected_signature_location
    user = UserFactory()

    # instantiate the view
    view = RenewableMetterReadingFormView()

    # create delivery points for entity
    assert DeliveryPoint.objects.all().count() == 0
    entity_name = "entity-1"
    entity = EntityFactory(users=(user,), name=entity_name)
    size = 4
    DeliveryPointFactory.create_batch(
        size=size,
        entity=entity,
        has_renewable=True,
        is_active=True,
    )
    expected_renewable_dps = entity.get_unsubmitted_quarterly_renewables()
    assert DeliveryPoint.objects.all().count() == size

    # accessing the view and get context data
    request = rf.get(reverse("renewable:manage"), kwargs={"slug": entity_name})
    request.user = user
    view.setup(request, slug=entity_name)
    context = view.get_context_data()
    assert context.get("entity") == entity
    assert context.get("signature_location") == expected_signature_location
    renewable_dps = context.get("renewable_delivery_points")
    assert renewable_dps.count() == size
    for renewable, expected_renewable in zip(
        renewable_dps, expected_renewable_dps, strict=True
    ):
        assert renewable.id == expected_renewable.id
