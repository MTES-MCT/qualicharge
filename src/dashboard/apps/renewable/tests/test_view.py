"""Dashboard renewable views tests."""

import datetime
from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.auth.factories import UserFactory
from apps.auth.mixins import UserValidationMixin
from apps.core.factories import DeliveryPointFactory, EntityFactory
from apps.core.mixins import EntityMixin
from apps.core.models import DeliveryPoint
from apps.renewable.models import Renewable
from apps.renewable.views import RenewableMetterReadingFormView, SubmittedRenewableView


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


def _setup_bulk_update_renewables_test_data(user, entity_name, size):
    """Fixture to setup bulk_update_renewables() test data."""
    entity = EntityFactory(users=(user,), name=entity_name)

    assert DeliveryPoint.objects.all().count() == 0
    DeliveryPointFactory.create_batch(
        size=size,
        entity=entity,
        has_renewable=True,
        is_active=True,
    )
    assert DeliveryPoint.objects.all().count() == size

    return entity.get_unsubmitted_quarterly_renewables()


@pytest.mark.django_db
def test_manage_views_bulk_update_renewables(rf):
    """Test bulk_update_renewables() method of RenewableMetterReadingFormView."""
    SIZE = 4
    ENTITY_NAME = "entity-1"
    VALID_DATE = "2025-04-24"
    VALID_READING = 45

    # setup data
    user = UserFactory()
    expected_renewable_dps = _setup_bulk_update_renewables_test_data(
        user, ENTITY_NAME, SIZE
    )

    # instantiate the view
    url = reverse("renewable:manage", kwargs={"slug": ENTITY_NAME})
    view = RenewableMetterReadingFormView()
    request = rf.post(url)
    request.user = user

    # get expected renewable to post
    expected_renewable = expected_renewable_dps.first()

    # 1 - test empty form should create nothing
    posted_data = {}
    mock_form = MagicMock(cleaned_data=posted_data)
    view.setup(request, slug=ENTITY_NAME, POST=posted_data)
    result = view._bulk_create_renewables([], mock_form)
    assert result == []

    # 2 - test adding a statement that does not belong to the user should create nothing
    user2 = UserFactory()
    entity2 = EntityFactory(users=(user2,))
    wrong_dp = DeliveryPointFactory(entity=entity2, has_renewable=True, is_active=True)
    posted_data = {
        "delivery_point_ids": [str(wrong_dp.id)],
        f"collected_at_{expected_renewable.id}": VALID_DATE,
        f"meter_reading_{expected_renewable.id}": VALID_READING,
        "has_confirmed_information_accuracy": True,
    }
    wrong_dps = DeliveryPoint.objects.filter(id=wrong_dp.id)
    mock_form = MagicMock(cleaned_data=posted_data)
    view.setup(request, slug=ENTITY_NAME, POST=posted_data)
    result = view._bulk_create_renewables(wrong_dps, mock_form)
    assert len(result) == 0
    assert Renewable.objects.all().count() == 0

    # 3 - test adding one statement
    posted_data = {
        "delivery_point_ids": [str(expected_renewable.id)],
        f"collected_at_{expected_renewable.id}": VALID_DATE,
        f"meter_reading_{expected_renewable.id}": VALID_READING,
        "has_confirmed_information_accuracy": True,
    }
    mock_form = MagicMock(cleaned_data=posted_data)
    view.setup(request, slug=ENTITY_NAME, POST=posted_data)
    result = view._bulk_create_renewables(expected_renewable_dps, mock_form)
    assert len(result) == 1
    assert result[0].delivery_point_id == expected_renewable.id
    assert result[0].collected_at == datetime.datetime.strptime(VALID_DATE, "%Y-%m-%d")
    assert result[0].meter_reading == float(VALID_READING)
    assert result[0].has_confirmed_information_accuracy is True
    assert Renewable.objects.all().count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "no_meter_reading",
    [
        {
            "collected_at": "2025-04-24",
            "meter_reading": None,
            "has_confirmed_information_accuracy": True,
        },
        {
            "collected_at": "2025-04-24",
            "meter_reading": "",
            "has_confirmed_information_accuracy": True,
        },
    ],
)
def test_manage_views_bulk_update_renewables_with_no_meter_reading(
    rf, no_meter_reading
):
    """Test bulk_update_renewables() with invalid inputs."""
    # setup data
    size = 4
    entity_name = "entity-1"
    user = UserFactory()
    expected_renewable_dps = _setup_bulk_update_renewables_test_data(
        user, entity_name, size
    )

    # instantiate the view
    url = reverse("renewable:manage", kwargs={"slug": entity_name})
    view = RenewableMetterReadingFormView()
    request = rf.post(url)
    request.user = user

    # get renewable to post
    renewable = expected_renewable_dps.first()
    posted_data = {"delivery_point_ids": [str(renewable.id)]}

    for key, value in no_meter_reading.items():
        if key == "meter_reading":
            posted_data[f"meter_reading_{renewable.id}"] = value
        elif key == "collected_at":
            posted_data[f"collected_at_{renewable.id}"] = value

    mock_form = MagicMock(cleaned_data=posted_data)
    view.setup(request, slug=entity_name, POST=posted_data)

    result = view._bulk_create_renewables(expected_renewable_dps, mock_form)
    assert len(result) == 0
    assert Renewable.objects.all().count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid_input",
    [
        {
            "collected_at": "2025-04-24",
            "meter_reading": -45,
            "has_confirmed_information_accuracy": True,
        },
        {
            "collected_at": "2025-04-24",
            "meter_reading": "azerty",
            "has_confirmed_information_accuracy": True,
        },
        {
            "collected_at": None,
            "meter_reading": 45,
            "has_confirmed_information_accuracy": True,
        },
        {
            "collected_at": "2025-04-24",
            "meter_reading": 45,
            "has_confirmed_information_accuracy": False,
        },
    ],
)
def test_manage_views_bulk_update_renewables_invalid_inputs(rf, invalid_input):
    """Test bulk_update_renewables() with invalid inputs."""
    # setup data
    size = 4
    entity_name = "entity-1"
    user = UserFactory()
    expected_renewable_dps = _setup_bulk_update_renewables_test_data(
        user, entity_name, size
    )

    # instantiate the view
    url = reverse("renewable:manage", kwargs={"slug": entity_name})
    view = RenewableMetterReadingFormView()
    request = rf.post(url)
    request.user = user

    # get renewable to post
    renewable = expected_renewable_dps.first()
    posted_data = {"delivery_point_ids": [str(renewable.id)]}

    for key, value in invalid_input.items():
        if key == "meter_reading":
            posted_data[f"meter_reading_{renewable.id}"] = value
        elif key == "collected_at":
            posted_data[f"collected_at_{renewable.id}"] = value

    mock_form = MagicMock(cleaned_data=posted_data)
    view.setup(request, slug=entity_name, POST=posted_data)

    with pytest.raises(ValidationError):
        result = view._bulk_create_renewables(expected_renewable_dps, mock_form)
        assert len(result) == 0
    assert Renewable.objects.all().count() == 0


@pytest.mark.django_db
def test_submitted_renewable_view_inherits_mixins():
    """Test SubmittedRenewableView inherits mixins."""
    assert issubclass(SubmittedRenewableView, EntityMixin)
    assert issubclass(SubmittedRenewableView, UserValidationMixin)
