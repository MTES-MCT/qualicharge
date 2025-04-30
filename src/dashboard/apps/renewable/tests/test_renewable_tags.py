"""Dashboard renewable_tags tests."""

from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from django.utils.safestring import SafeString

from apps.core.factories import DeliveryPointFactory, EntityFactory, StationFactory
from apps.renewable.factories import RenewableFactory
from apps.renewable.models import Renewable
from apps.renewable.templatetags.renewable_tags import (
    format_quarter_display_string,
    sort_submitted_renewable_by_station,
)

QUARTER_TEST_CASES = [
    {
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 3, 31),
        "quarter": 1,
        "expected": "1st quarter 2025  <br />01/01/2025 to 31/03/2025",
    },
    {
        "start_date": date(2025, 4, 1),
        "end_date": date(2025, 6, 30),
        "quarter": 2,
        "expected": "2nd quarter 2025  <br />01/04/2025 to 30/06/2025",
    },
    {
        "start_date": date(2025, 7, 1),
        "end_date": date(2025, 9, 30),
        "quarter": 3,
        "expected": "3rd quarter 2025  <br />01/07/2025 to 30/09/2025",
    },
    {
        "start_date": date(2025, 10, 1),
        "end_date": date(2025, 12, 31),
        "quarter": 4,
        "expected": "4th quarter 2025  <br />01/10/2025 to 31/12/2025",
    },
]


@pytest.mark.django_db
@pytest.mark.parametrize("test_case", QUARTER_TEST_CASES)
@patch("apps.renewable.templatetags.renewable_tags.get_quarter_number")
@patch("apps.renewable.templatetags.renewable_tags.get_previous_quarter_date_range")
def test_quarter_period_returns_safe_string(
    mock_get_previous_quarter_date_range, mock_get_quarter_number, test_case
):
    """Test quarter_period_returns_safe_string() returns SafeString."""
    mock_get_previous_quarter_date_range.return_value = (
        test_case["start_date"],
        test_case["end_date"],
    )
    mock_get_quarter_number.return_value = test_case["quarter"]

    result = format_quarter_display_string(
        test_case["start_date"], test_case["end_date"], test_case["quarter"]
    )

    assert isinstance(result, SafeString)
    assert test_case["expected"] in result


@pytest.mark.django_db
def test_sort_submitted_renewable_by_station():
    """Test `sort_submitted_renewable_by_station` function."""
    # test order_consents_by_station() without station
    renewables = Renewable.objects.all()
    assert renewables.count() == 0
    results = sort_submitted_renewable_by_station(renewables)
    assert results == []

    # create entity, delivery points, consents and stations
    entity1 = EntityFactory()
    dp_1 = DeliveryPointFactory(entity=entity1)
    dp_2 = DeliveryPointFactory(entity=entity1)
    dp_3 = DeliveryPointFactory(entity=entity1)

    # stations are created in a non-alphabetical order
    StationFactory(
        delivery_point=dp_1, station_name="B", id_station_itinerance="FRABCP01"
    )
    StationFactory(
        delivery_point=dp_2, station_name="C", id_station_itinerance="FRDEFP05"
    )
    StationFactory(
        delivery_point=dp_2, station_name="y", id_station_itinerance="FRDEFP02"
    )
    StationFactory(
        delivery_point=dp_2, station_name="A", id_station_itinerance="FRDEFP03"
    )
    StationFactory(
        delivery_point=dp_2, station_name="p", id_station_itinerance="FRDEFP04"
    )
    StationFactory(
        delivery_point=dp_3, station_name="d", id_station_itinerance="FRGHIP01"
    )

    # create submitted renewables (in order of collected date and station name)
    r1 = RenewableFactory(
        delivery_point=dp_2, collected_at="2025-03-21", meter_reading=99
    )
    r2 = RenewableFactory(
        delivery_point=dp_1, collected_at="2025-03-21", meter_reading=99
    )
    r3 = RenewableFactory(
        delivery_point=dp_3, collected_at="2025-03-21", meter_reading=99
    )

    r4 = RenewableFactory(
        delivery_point=dp_2, collected_at="2024-06-21", meter_reading=99
    )
    r5 = RenewableFactory(
        delivery_point=dp_1, collected_at="2024-06-21", meter_reading=99
    )
    r6 = RenewableFactory(
        delivery_point=dp_3, collected_at="2024-06-21", meter_reading=99
    )

    r7 = RenewableFactory(
        delivery_point=dp_2, collected_at="2024-03-21", meter_reading=99
    )
    r8 = RenewableFactory(
        delivery_point=dp_1, collected_at="2024-03-21", meter_reading=99
    )
    r9 = RenewableFactory(
        delivery_point=dp_3, collected_at="2024-03-21", meter_reading=99
    )

    renewables = Renewable.objects.all()
    expected_renewables_count = 9
    assert renewables.count() == expected_renewables_count
    results = sort_submitted_renewable_by_station(renewables)

    # Extract id, station_name and id_station_itinerance from grouped stations
    # for comparison.
    ordered_renewables = [
        {
            "id": item["id"],
            "collected_at": item["collected_at"],
            "stations_grouped": item["stations_grouped"],
        }
        for item in results
    ]

    format = "%Y-%m-%d"
    expected_date_1 = datetime.strptime("2025-03-21", format).replace(
        tzinfo=timezone.utc
    )
    expected_date_2 = datetime.strptime("2024-06-21", format).replace(
        tzinfo=timezone.utc
    )
    expected_date_3 = datetime.strptime("2024-03-21", format).replace(
        tzinfo=timezone.utc
    )

    assert ordered_renewables == [
        {
            "id": r1.id,
            "collected_at": expected_date_1,
            "stations_grouped": {
                "A": ["FRDEFP03"],
                "C": ["FRDEFP05"],
                "p": ["FRDEFP04"],
                "y": ["FRDEFP02"],
            },
        },
        {
            "id": r2.id,
            "collected_at": expected_date_1,
            "stations_grouped": {"B": ["FRABCP01"]},
        },
        {
            "id": r3.id,
            "collected_at": expected_date_1,
            "stations_grouped": {"d": ["FRGHIP01"]},
        },
        {
            "id": r4.id,
            "collected_at": expected_date_2,
            "stations_grouped": {
                "A": ["FRDEFP03"],
                "C": ["FRDEFP05"],
                "p": ["FRDEFP04"],
                "y": ["FRDEFP02"],
            },
        },
        {
            "id": r5.id,
            "collected_at": expected_date_2,
            "stations_grouped": {"B": ["FRABCP01"]},
        },
        {
            "id": r6.id,
            "collected_at": expected_date_2,
            "stations_grouped": {"d": ["FRGHIP01"]},
        },
        {
            "id": r7.id,
            "collected_at": expected_date_3,
            "stations_grouped": {
                "A": ["FRDEFP03"],
                "C": ["FRDEFP05"],
                "p": ["FRDEFP04"],
                "y": ["FRDEFP02"],
            },
        },
        {
            "id": r8.id,
            "collected_at": expected_date_3,
            "stations_grouped": {"B": ["FRABCP01"]},
        },
        {
            "id": r9.id,
            "collected_at": expected_date_3,
            "stations_grouped": {"d": ["FRGHIP01"]},
        },
    ]
