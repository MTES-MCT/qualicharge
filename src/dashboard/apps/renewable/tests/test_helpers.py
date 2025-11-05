"""Dashboard renewable helpers tests."""

from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest
from django.db.models import QuerySet
from django.utils import timezone as django_timezone

from apps.auth.factories import UserFactory
from apps.core.factories import DeliveryPointFactory, EntityFactory, StationFactory
from apps.core.models import DeliveryPoint, Entity
from apps.renewable.helpers import (
    get_opening_period_dates,
    is_in_opening_period,
    send_notification_for_opening,
    sort_delivery_points_by_station,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "current_date, opening_period_days, expected_first_day, expected_last_day",
    [
        (date(2025, 1, 1), 15, date(2025, 1, 1), date(2025, 1, 15)),
        (date(2025, 6, 15), 30, date(2025, 4, 1), date(2025, 4, 30)),
        (date(2025, 12, 1), 7, date(2025, 10, 1), date(2025, 10, 7)),
    ],
)
def test_get_opening_period_dates_valid_date(  # noqa: PLR0913
    monkeypatch,
    settings,
    current_date,
    opening_period_days,
    expected_first_day,
    expected_last_day,
):
    """Test if a date is in the opening period."""
    monkeypatch.setattr(django_timezone, "now", lambda: current_date)
    settings.RENEWABLE_OPENING_PERIOD_DAYS = opening_period_days

    first_day, last_day = get_opening_period_dates()
    assert first_day == expected_first_day
    assert last_day == expected_last_day


@pytest.mark.django_db
@pytest.mark.parametrize(
    "days_delta, expected_result",
    [
        (1, True),  # the exact first day of the period
        (10, True),  # within the opening period
        (15, True),  # last day of the opening period
        (20, False),  # outside the opening period returns
        (-1, False),  # before the opening period
    ],
)
def test_is_in_opening_period_valid_date(
    monkeypatch,
    settings,
    days_delta,
    expected_result,
):
    """Test if a date is in the opening period."""
    monkeypatch.setattr(django_timezone, "now", lambda: datetime(2025, 1, 1))

    settings.RENEWABLE_OPENING_PERIOD_DAYS = 15
    now = django_timezone.now().date()
    test_date = now + timedelta(days=days_delta - 1)

    assert is_in_opening_period(test_date) is expected_result


@pytest.mark.django_db
def test_send_notification_for_opening(settings, monkeypatch):
    """Test send_notification_for_opening."""
    monkeypatch.setattr(django_timezone, "now", lambda: datetime(2025, 1, 1))
    settings.RENEWABLE_OPENING_PERIOD_DAYS = 15

    expected_template_id = 8
    expected_link = "https://example.com/consent"
    expected_support = "support@example.com"

    # setup email config
    settings.CONTACT_EMAIL = expected_support
    settings.DASHBOARD_EMAIL_RENEWABLE_OPENING_PERIOD = "renewable_opening_period"
    settings.DASHBOARD_EMAIL_CONFIGS = {
        "renewable_opening_period": {
            "template_id": expected_template_id,
            "link": expected_link,
        }
    }

    # create, users, entity and consents
    assert Entity.objects.count() == 0
    user = UserFactory(email="user@example.com")
    user2 = UserFactory(email="")
    entity = EntityFactory(users=[user, user2])
    DeliveryPointFactory(has_renewable=True, is_active=True, entity=entity)
    assert Entity.objects.count() == 1

    with patch("apps.renewable.helpers.AnymailMessage") as mock_message, patch(
        "apps.renewable.helpers.sentry_sdk.capture_message"
    ) as mock_sentry:
        email_send_mock = mock_message.return_value.send

        # test sending notifications
        send_notification_for_opening(entity)
        email_send_mock.assert_called_once()

        # notification sending should be called once with only
        # the first user information.
        mock_message.assert_called_once_with(
            to=[user.email],
            template_id=expected_template_id,
            merge_data={
                user.email: {
                    "last_name": user.last_name,
                    "first_name": user.first_name,
                    "link": expected_link,
                    "support_email": expected_support,
                    "start_period": "01/01/2025",
                    "end_period": "15/01/2025",
                }
            },
        )

        # user2 has no email, an error should be raised
        mock_sentry.assert_called_once_with(
            f"Email can't be send. User {user2.id} does not have an email address.",
            level="error",
        )

    # test sending notifications in not opening period should not send mail
    monkeypatch.setattr(django_timezone, "now", lambda: datetime(2025, 2, 6))
    send_notification_for_opening(entity)

    # test sending notifications for entity without renewables should not send mail
    entity_without_renewable = EntityFactory(users=[user])
    DeliveryPointFactory(entity=entity_without_renewable, has_renewable=False)
    with patch("apps.renewable.helpers.AnymailMessage") as mock_message:
        email_send_mock = mock_message.return_value.send
        send_notification_for_opening(entity_without_renewable)
        email_send_mock.assert_not_called()


@pytest.mark.django_db
def test_sort_delivery_points_by_station():
    """Test that delivery points are sorted by first station name.

    Test with uppercase and lowercase stations and delivery points without stations.
    """
    # create, users, entity and consents
    assert Entity.objects.count() == 0
    user = UserFactory(email="user@example.com")
    user2 = UserFactory(email="")
    entity = EntityFactory(users=[user, user2])
    assert Entity.objects.count() == 1

    # Create in reverse order
    assert DeliveryPoint.objects.count() == 0
    dp_z = DeliveryPointFactory(entity=entity, is_active=True)
    StationFactory(station_name="z-station", delivery_point=dp_z)

    dp_without = DeliveryPointFactory(entity=entity, is_active=True)

    dp_b_upper_case = DeliveryPointFactory(entity=entity, is_active=True)
    StationFactory(station_name="B-STATION", delivery_point=dp_b_upper_case)

    dp_a = DeliveryPointFactory(entity=entity, is_active=True)
    StationFactory(station_name="a-station", delivery_point=dp_a)

    dp_m = DeliveryPointFactory(entity=entity, is_active=True)
    StationFactory(station_name="m-station", delivery_point=dp_m)

    expected_dps_count = 5
    assert DeliveryPoint.objects.count() == expected_dps_count

    # Get unsorted queryset
    unsorted = entity.delivery_points.filter(is_active=True)

    # Sort
    sorted_qs = sort_delivery_points_by_station(unsorted)
    sorted_list = list(sorted_qs)

    # Verify order
    assert sorted_list[0].pk == dp_a.pk
    assert sorted_list[1].pk == dp_b_upper_case.pk
    assert sorted_list[2].pk == dp_m.pk
    assert sorted_list[3].pk == dp_z.pk
    assert sorted_list[4].pk == dp_without.pk

    # the function returns a QuerySet
    assert isinstance(sorted_qs, QuerySet)
    assert hasattr(sorted_qs, "ordered")
