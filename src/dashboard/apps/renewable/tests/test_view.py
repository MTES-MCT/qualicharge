"""Dashboard renewable views tests."""

from datetime import date
from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.auth.factories import UserFactory
from apps.auth.mixins import UserValidationMixin
from apps.core.factories import DeliveryPointFactory, EntityFactory
from apps.core.mixins import EntityViewMixin
from apps.core.models import DeliveryPoint
from apps.renewable.models import Renewable
from apps.renewable.views import RenewableMetterReadingFormView


@pytest.mark.django_db
def test_view_inherits_entity_mixin():
    """Test RenewableMetterReadingFormView inherits mixins."""
    assert issubclass(RenewableMetterReadingFormView, EntityViewMixin)
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
    """Test manage view with data."""
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


@pytest.mark.django_db
def test_manage_views_post(client, monkeypatch):
    """Test post() method of RenewableMetterReadingFormView."""
    monkeypatch.setattr(timezone, "now", lambda: date(2025, 5, 6))
    ENTITY_NAME = "entity-1"
    expected_renewable_count = 2
    expected_renewable_metter_reading_0 = 100.5
    expected_renewable_metter_reading_1 = 99.5

    user = UserFactory()
    entity = EntityFactory(users=(user,), name=ENTITY_NAME)
    dp = DeliveryPointFactory(entity=entity, has_renewable=True, is_active=True)
    dp2 = DeliveryPointFactory(entity=entity, has_renewable=True, is_active=True)

    form_data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-delivery_point": dp.id,
        "form-0-meter_reading": expected_renewable_metter_reading_0,
        "form-0-collected_at": timezone.now().strftime("%Y-%m-%d"),
        "form-1-delivery_point": dp2.id,
        "form-1-meter_reading": expected_renewable_metter_reading_1,
        "form-1-collected_at": timezone.now().strftime("%Y-%m-%d"),
        "has_confirmed_information_accuracy": True,
    }

    client.force_login(user)

    assert Renewable.objects.count() == 0
    response = client.post(
        reverse("renewable:manage", kwargs={"slug": ENTITY_NAME}), data=form_data
    )

    assert response.status_code == HTTPStatus.FOUND
    assert Renewable.objects.count() == expected_renewable_count

    renewable = Renewable.objects.get(delivery_point=dp)
    assert renewable.meter_reading == expected_renewable_metter_reading_0

    renewable = Renewable.objects.get(delivery_point=dp2)
    assert renewable.meter_reading == expected_renewable_metter_reading_1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "meter_reading, collected_at, has_confirmed, form_error_key",
    [
        # test case for meter_reading
        ("abc", "2024-03-20 10:00:00", True, "meter_reading"),
        ("-100", "2024-03-20 10:00:00", True, "meter_reading"),
        # test case for collected_at
        ("100.5", None, True, "collected_at"),
        ("100.5", "invalid_date", True, "collected_at"),
        ("100.5", "2099-03-20 10:00:00", True, "collected_at"),  # in futur
        ("100.5", "2024-03-20 10:00:00", True, "collected_at"),  # in past
    ],
)
def test_manage_views_post_with_invalid_data(  # noqa: PLR0913
    meter_reading,
    collected_at,
    has_confirmed,
    form_error_key,
    client,
    monkeypatch,
):
    """Test post() method of RenewableMetterReadingFormView with invalid data."""
    monkeypatch.setattr(timezone, "now", lambda: date(2025, 5, 6))
    ENTITY_NAME = "entity-1"

    user = UserFactory()
    entity = EntityFactory(users=(user,), name=ENTITY_NAME)
    dp = DeliveryPointFactory(entity=entity, has_renewable=True, is_active=True)

    form_data = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-delivery_point": dp.id,
    }

    if meter_reading is not None:
        form_data["form-0-meter_reading"] = meter_reading

    if collected_at is not None:
        form_data["form-0-collected_at"] = collected_at

    if has_confirmed is not None:
        form_data["form-0-has_confirmed_information_accuracy"] = has_confirmed

    assert Renewable.objects.count() == 0
    client.force_login(user)
    response = client.post(
        reverse("renewable:manage", kwargs={"slug": ENTITY_NAME}), data=form_data
    )
    assert response.status_code == HTTPStatus.OK
    assert Renewable.objects.count() == 0

    formset = response.context["formset"]
    assert formset.errors[0].get(form_error_key) is not None
