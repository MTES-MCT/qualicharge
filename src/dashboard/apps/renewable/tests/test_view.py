"""Dashboard renewable views tests."""

import datetime as dt
from datetime import date, datetime
from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.conf import settings as django_settings
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.auth.factories import UserFactory
from apps.auth.mixins import UserValidationMixin
from apps.core.factories import DeliveryPointFactory, EntityFactory, StationFactory
from apps.core.mixins import EntityViewMixin
from apps.core.models import DeliveryPoint
from apps.renewable.factories import RenewableFactory
from apps.renewable.models import Renewable
from apps.renewable.views import (
    DeliveryPointRenewableFormSetView,
    RenewableMetterReadingFormView,
    SubmittedRenewableView,
)


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
    # collected date should be within x days prior to the previous quarter's end date
    expected_collected_at = datetime(2025, 3, 28, tzinfo=dt.timezone.utc).date()

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
        "form-0-collected_at": expected_collected_at,
        "form-1-delivery_point": dp2.id,
        "form-1-meter_reading": expected_renewable_metter_reading_1,
        "form-1-collected_at": expected_collected_at,
        "has_confirmed_information_accuracy": True,
    }

    client.force_login(user)

    assert Renewable.objects.count() == 0
    response = client.post(
        reverse("renewable:manage", kwargs={"slug": ENTITY_NAME}),
        data=form_data,
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


@pytest.mark.django_db
def test_submitted_renewable_view_inherits_mixins():
    """Test SubmittedRenewableView inherits mixins."""
    assert issubclass(SubmittedRenewableView, EntityViewMixin)
    assert issubclass(SubmittedRenewableView, UserValidationMixin)


@pytest.mark.django_db
def test_sort_submitted_renewable_by_station():
    """Test `sort_submitted_renewable_by_station` function."""
    # test order_consents_by_station() without station
    renewables = Renewable.objects.all()
    assert renewables.count() == 0
    queryset = Renewable.objects.all()
    result = SubmittedRenewableView._order_by_quarter_stations(queryset)
    assert result == []

    # create entity, delivery points, consents and stations
    entity1 = EntityFactory()
    dp_1 = DeliveryPointFactory(entity=entity1)
    StationFactory(delivery_point=dp_1, station_name="B", id_station_itinerance="FRA01")
    StationFactory(delivery_point=dp_1, station_name="c", id_station_itinerance="FRD05")

    dp_2 = DeliveryPointFactory(entity=entity1)
    StationFactory(delivery_point=dp_2, station_name="A", id_station_itinerance="FRD03")
    StationFactory(delivery_point=dp_2, station_name="P", id_station_itinerance="FRD04")

    dp_3 = DeliveryPointFactory(entity=entity1)
    StationFactory(delivery_point=dp_3, station_name="j", id_station_itinerance="FRG01")

    # create submitted renewables (in order of collected date and station name)
    r1 = RenewableFactory(delivery_point=dp_2, collected_at="2025-03-21")
    r2 = RenewableFactory(delivery_point=dp_1, collected_at="2025-03-21")
    r3 = RenewableFactory(delivery_point=dp_2, collected_at="2024-06-21")
    r4 = RenewableFactory(delivery_point=dp_3, collected_at="2024-06-21")
    r5 = RenewableFactory(delivery_point=dp_1, collected_at="2024-03-21")
    r6 = RenewableFactory(delivery_point=dp_3, collected_at="2024-03-21")

    expected_renewables_count = 6
    queryset = Renewable.objects.all()
    assert renewables.count() == expected_renewables_count
    result = SubmittedRenewableView._order_by_quarter_stations(queryset)

    # Extract id, collected_at and stations_grouped from result for comparison
    ordered_renewables = [
        {
            "id": item["id"],
            "stations_grouped": item["stations_grouped"],
        }
        for item in result
    ]

    assert ordered_renewables == [
        {"id": r1.id, "stations_grouped": {"A": ["FRD03"], "P": ["FRD04"]}},
        {"id": r2.id, "stations_grouped": {"B": ["FRA01"], "c": ["FRD05"]}},
        {"id": r3.id, "stations_grouped": {"A": ["FRD03"], "P": ["FRD04"]}},
        {"id": r4.id, "stations_grouped": {"j": ["FRG01"]}},
        {"id": r5.id, "stations_grouped": {"B": ["FRA01"], "c": ["FRD05"]}},
        {"id": r6.id, "stations_grouped": {"j": ["FRG01"]}},
    ]


@pytest.mark.django_db
def test_send_email_notification_populated(monkeypatch, rf):
    """Test `_send_email` is sent."""
    monkeypatch.setattr(timezone, "now", lambda: date(2025, 5, 6))
    entity_name = "entity-1"

    user = UserFactory()
    expected_renewable_metter_reading = 100.5

    entity = EntityFactory(users=(user,), name=entity_name)
    dp = DeliveryPointFactory(entity=entity, has_renewable=True, is_active=True)

    form_data = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-delivery_point": dp.id,
        "form-0-meter_reading": expected_renewable_metter_reading,
        "form-0-collected_at": timezone.now().strftime("%Y-%m-%d"),
        "form-1-collected_at": timezone.now().strftime("%Y-%m-%d"),
        "has_confirmed_information_accuracy": True,
    }

    request = rf.post(
        reverse("renewable:manage", kwargs={"slug": entity_name}), data=form_data
    )
    request.user = user

    view = RenewableMetterReadingFormView()
    view.setup(request)

    with patch("apps.renewable.views.AnymailMessage") as mock_message:
        email_send_mock = mock_message.return_value.send
        view._send_email()

        email_config_name = django_settings.DASHBOARD_EMAIL_RENEWABLE_SUBMISSION
        email_config = django_settings.DASHBOARD_EMAIL_CONFIGS[email_config_name]

        mock_message.assert_called_once_with(
            to=[user.email],
            template_id=email_config.get("template_id"),
            merge_data={
                user.email: {
                    "last_name": user.last_name,
                    "first_name": user.first_name,
                    "start_period": "01/01/2025",
                    "end_period": "31/03/2025",
                    "link": email_config.get("link"),
                }
            },
        )
        email_send_mock.assert_called_once()


@pytest.mark.django_db
def test_delivery_point_renewable_formset_view_inherits_mixins():
    """Test DeliveryPointRenewableFormSetView inherits mixins."""
    assert issubclass(DeliveryPointRenewableFormSetView, EntityViewMixin)
    assert issubclass(DeliveryPointRenewableFormSetView, UserValidationMixin)


@pytest.mark.django_db
def test_delivery_point_renewable_formset_view_without_slug_is_redirected(client):
    """Test direct access to renewable:delivery-points is redirected to index."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("renewable:delivery-points"))
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("renewable:index")


@pytest.mark.django_db
def test_delivery_point_renewable_formset_view_with_wrong_slug_raised_404(client):
    """Test direct access to renewable:manage is redirected to index."""
    user = UserFactory()
    client.force_login(user)

    entity_name = "entity-1"
    wrong_slug = "wrong-slug"
    EntityFactory(name=entity_name, users=[user])

    url = reverse("renewable:delivery-points", kwargs={"slug": wrong_slug})
    response = client.get(url)

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_delivery_point_renewable_formset_view_without_data(client):
    """Test DeliveryPointRenewableFormSetView without data."""
    user = UserFactory()
    client.force_login(user)

    entity_name = "entity-1"
    EntityFactory(name=entity_name, users=[user])
    url = reverse("renewable:delivery-points", kwargs={"slug": entity_name})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    # force template rendering
    rendered = response.render()
    html = rendered.content.decode()

    expected_html_id = 'id="no-data-card"'
    assert (expected_html_id in html) is True


@pytest.mark.django_db
def test_delivery_point_renewable_formset_view_with_data(client):
    """Test DeliveryPointRenewableFormSetView with data."""
    user = UserFactory()
    client.force_login(user)

    # create entity and associated delivery points
    assert DeliveryPoint.objects.all().count() == 0
    entity_name = "entity-1"
    entity = EntityFactory(name=entity_name, users=[user])

    size = 2
    dps = DeliveryPointFactory.create_batch(
        size=size,
        entity=entity,
        has_renewable=True,
        is_active=True,
    )
    dp_3 = DeliveryPointFactory(entity=entity, has_renewable=False, is_active=True)
    # create an inactive delivery point. It should not be listed.
    dp_4 = DeliveryPointFactory(entity=entity, has_renewable=True, is_active=False)
    expected_size = 4
    assert DeliveryPoint.objects.all().count() == expected_size

    # render manage view
    url = reverse("renewable:delivery-points", kwargs={"slug": entity_name})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    # force template rendering
    rendered = response.render()
    html = rendered.content.decode()

    # add all created delivery points to the list
    active_dps = dps + [dp_3]
    # test all delivery points are listed
    assert all(str(dp.provider_assigned_id) in html for dp in active_dps)
    assert dp_4.provider_assigned_id not in html


@pytest.mark.django_db
def test_delivery_point_renewable_formset_view_get_context_data(client):
    """Test get_context_data() method of DeliveryPointRenewableFormSetView."""
    user = UserFactory()
    client.force_login(user)

    # create entity
    entity_name = "entity-1"
    entity = EntityFactory(name=entity_name, users=[user])

    # create delivery points
    assert DeliveryPoint.objects.all().count() == 0
    dp1 = DeliveryPointFactory(entity=entity, has_renewable=True, is_active=True)
    dp2 = DeliveryPointFactory(entity=entity, has_renewable=False, is_active=True)
    # create an inactive delivery point. It should not be listed.
    DeliveryPointFactory(entity=entity, has_renewable=True, is_active=False)
    expected_size = 3
    assert DeliveryPoint.objects.all().count() == expected_size

    # accessing the view and get context data
    url = reverse("renewable:delivery-points", kwargs={"slug": entity_name})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    # check context
    context = response.context
    expected_dp_context_size = 2
    assert "entity" in context
    assert "formset" in context
    assert "delivery_points" in context

    # check context values
    assert context["entity"] == entity

    # check delivery points
    delivery_points = context["delivery_points"]
    assert delivery_points.count() == expected_dp_context_size
    assert set(delivery_points) == {dp1, dp2}

    # check formset
    formset = context["formset"]
    assert len(formset.forms) == expected_dp_context_size
    for form in formset.forms:
        assert hasattr(form, "delivery_point_obj")
        assert hasattr(form, "stations_grouped")
        assert form.delivery_point_obj in [dp1, dp2]


@pytest.mark.django_db
def test_delivery_point_renewable_formset_view_post_not_found(rf):
    """Test if post method raises Http404 when entity is not found."""
    user = UserFactory()
    entity_name = "no-entity"
    url = reverse("renewable:delivery-points", kwargs={"slug": entity_name})
    request = rf.post(url)
    request.user = user
    view = DeliveryPointRenewableFormSetView()
    view.request = request
    view.kwargs = {"slug": entity_name}

    with pytest.raises(Http404):
        view.post(request)


@pytest.mark.django_db
def test_delivery_point_renewable_formset_view_post(client):
    """Test if post method handles formset.

    Test `has_renewable` state changes for delivery points:
        - dp0: initial=True, form=True → expected=True
        - dp1: initial=False, form=True → expected=True
        - dp2: initial=True, form=False → expected=False
    """
    entity_name = "entity-1"

    user = UserFactory()
    entity = EntityFactory(users=(user,), name=entity_name)
    dp0 = DeliveryPointFactory(entity=entity, has_renewable=True, is_active=True)
    dp1 = DeliveryPointFactory(entity=entity, has_renewable=False, is_active=True)
    dp2 = DeliveryPointFactory(entity=entity, has_renewable=True, is_active=True)

    form_data = {
        "form-TOTAL_FORMS": "3",
        "form-INITIAL_FORMS": "3",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-id": dp0.id,
        "form-0-has_renewable": True,
        "form-0-entity_id": entity.id,
        "form-1-id": dp1.id,
        "form-1-has_renewable": True,
        "form-1-entity_id": entity.id,
        "form-2-id": dp2.id,
        "form-2-has_renewable": False,
        "form-2-entity_id": entity.id,
    }

    client.force_login(user)

    response = client.post(
        reverse("renewable:delivery-points", kwargs={"slug": entity_name}),
        data=form_data,
    )

    assert response.status_code == HTTPStatus.OK

    dp0.refresh_from_db()
    assert dp0.has_renewable is True

    dp1.refresh_from_db()
    assert dp1.has_renewable is True

    dp2.refresh_from_db()
    assert dp2.has_renewable is False
