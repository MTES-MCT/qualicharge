"""Dashboard renewable forms tests."""

import datetime as dt
from datetime import date, datetime, timedelta

import pytest
from django import forms
from django.forms import modelformset_factory
from django.utils import timezone

from apps.consent.tests.conftest import patch_datetime_now  # noqa: F401
from apps.core.factories import DeliveryPointFactory
from apps.renewable.forms import RenewableForm, RenewableFormSet
from apps.renewable.models import Renewable


def test_get_authorized_date_range(monkeypatch, settings):
    """Test _get_authorized_date_range()."""
    settings.RENEWABLE_MIN_DAYS_FOR_METER_READING = 15
    mock_now = date(2025, 3, 6)
    monkeypatch.setattr(timezone, "now", lambda: mock_now)

    min_date, end_date = RenewableForm._get_authorized_date_range()

    # expected dates
    expected_min_date = date(2024, 12, 16)
    expected_end_date = date(2024, 12, 31)
    assert min_date == expected_min_date
    assert end_date == expected_end_date

    # check min_date is before end_date
    assert min_date < end_date

    # check the gap between min_date and end_date
    delta = end_date - min_date
    assert delta.days == settings.RENEWABLE_MIN_DAYS_FOR_METER_READING


@pytest.mark.parametrize(
    "test_date,expected_quarter_end",
    [
        (date(2025, 2, 15), date(2024, 12, 31)),
        (date(2025, 5, 15), date(2025, 3, 31)),
        (date(2025, 8, 15), date(2025, 6, 30)),
        (date(2025, 11, 15), date(2025, 9, 30)),
    ],
)
def test_get_authorized_date_range_different_quarters(
    test_date, expected_quarter_end, monkeypatch, settings
):
    """Test _get_authorized_date_range() with different quarters."""
    monkeypatch.setattr(timezone, "now", lambda: test_date)

    min_date, end_date = RenewableForm._get_authorized_date_range()

    assert end_date == expected_quarter_end
    assert min_date == end_date - timedelta(
        days=settings.RENEWABLE_MIN_DAYS_FOR_METER_READING
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "collected_at, meter_reading, expected_message",
    [
        (None, 100.5, "Collected date is required if a meter reading is provided"),
        (
            "2999-01-01",
            100.5,
            "The date cannot be in the future. <br />Collected date should be "
            "between 16/03/2025 and 31/03/2025.",
        ),
        (
            "2000-01-01",
            100.5,
            "The date cannot be earlier than 16/03/2025.<br />Collected date should"
            " be between 16/03/2025 and 31/03/2025.",
        ),
        (
            "2025-03-15",
            100.5,
            "The date cannot be earlier than 16/03/2025.<br />Collected date should"
            " be between 16/03/2025 and 31/03/2025.",
        ),
        (
            "2025-04-01",
            100.5,
            "The date cannot be in the future. <br />Collected date should be "
            "between 16/03/2025 and 31/03/2025.",
        ),
    ],
)
def test_renewable_form_clean_collected_at_with_errors(
    collected_at, meter_reading, expected_message, monkeypatch
):
    """Test _clean_collected_at."""
    now = datetime(2025, 5, 6, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(timezone, "now", lambda: now)
    form = RenewableForm()

    if collected_at:
        collected_at = datetime.strptime(collected_at, "%Y-%m-%d").date()

    form.cleaned_data = {"collected_at": collected_at, "meter_reading": 100.5}
    with pytest.raises(forms.ValidationError) as e:
        form.clean_collected_at()
    assert e.value.messages == [expected_message]


def test_renewable_form_clean_collected_at_valid(monkeypatch):
    """Test _clean_collected_at with valid data."""
    now = datetime(2025, 5, 6, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(timezone, "now", lambda: now)

    form = RenewableForm()
    # collected date should be within x days prior to the previous quarter's end date
    expected_collected_at = datetime(2025, 3, 28, tzinfo=dt.timezone.utc).date()
    form.cleaned_data = {"collected_at": expected_collected_at, "meter_reading": 100.5}

    assert form.clean_collected_at() == expected_collected_at


def setup_formset_class():
    """Fixture to setup RenewableFormset class."""
    return modelformset_factory(
        Renewable,
        form=RenewableForm,
        formset=RenewableFormSet,
        extra=1,
        fields=["delivery_point", "meter_reading", "collected_at"],
    )


@pytest.mark.django_db
def test_renewable_formset_clean_has_confirmed_information_accuracy():
    """Test clean_has_confirmed_information_accuracy."""
    FormsetClass = setup_formset_class()

    post_data = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
    }

    # missing has_confirmed_information_accuracy checkbox
    formset = FormsetClass(queryset=Renewable.objects.none(), data=post_data)
    with pytest.raises(forms.ValidationError) as exc_info:
        formset.clean_has_confirmed_information_accuracy()
    expected_message = "You must confirm the accuracy of the information"
    assert str(exc_info.value.messages[0]) == expected_message

    # has_confirmed_information_accuracy value is None
    post_data["has_confirmed_information_accuracy"] = None
    formset = FormsetClass(queryset=Renewable.objects.none(), data=post_data)
    with pytest.raises(forms.ValidationError) as exc_info:
        formset.clean_has_confirmed_information_accuracy()
    expected_message = "You must confirm the accuracy of the information"
    assert str(exc_info.value.messages[0]) == expected_message

    # has_confirmed_information_accuracy checkbox is checked
    post_data["has_confirmed_information_accuracy"] = "on"
    formset = FormsetClass(queryset=Renewable.objects.none(), data=post_data)
    result = formset.clean_has_confirmed_information_accuracy()
    assert result is True

    # has_confirmed_information_accuracy checkbox is not checked
    post_data["has_confirmed_information_accuracy"] = "off"
    formset = FormsetClass(queryset=Renewable.objects.none(), data=post_data)
    result = formset.clean_has_confirmed_information_accuracy()
    assert result is False


@pytest.mark.django_db
def test_renewable_formset_saves_multiple_meter_readings(monkeypatch):
    """Test save multiple meter readings in RenewableFormset."""
    now = datetime(2025, 5, 6, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(timezone, "now", lambda: now)

    dp1 = DeliveryPointFactory(has_renewable=True, is_active=True)
    dp2 = DeliveryPointFactory(has_renewable=True, is_active=True)

    expected_meter_reading_1 = 100.5
    expected_meter_reading_2 = 200.5
    # collected date should be within x days prior to the previous quarter's end date
    expected_collected_at = datetime(2025, 3, 28, tzinfo=dt.timezone.utc)
    expected_count = 2

    FormsetClass = setup_formset_class()
    formset = FormsetClass(
        queryset=Renewable.objects.none(),
        data={
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-delivery_point": dp1.id,
            "form-0-meter_reading": expected_meter_reading_1,
            "form-0-collected_at": expected_collected_at,
            "form-1-delivery_point": dp2.id,
            "form-1-meter_reading": expected_meter_reading_2,
            "form-1-collected_at": expected_collected_at,
            "has_confirmed_information_accuracy": "on",
        },
    )

    assert formset.is_valid()
    assert Renewable.objects.count() == 0
    instances = formset.save()
    assert len(instances) == expected_count
    assert Renewable.objects.count() == expected_count
    assert all(isinstance(instance, Renewable) for instance in instances)
    assert instances[0].meter_reading == expected_meter_reading_1
    assert instances[1].meter_reading == expected_meter_reading_2


@pytest.mark.django_db
def test_renewable_formset_save_partial_data_submission(monkeypatch):
    """Test save partial data submission in RenewableFormset."""
    now = datetime(2025, 5, 6, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(timezone, "now", lambda: now)

    dp1 = DeliveryPointFactory(has_renewable=True, is_active=True)
    dp2 = DeliveryPointFactory(has_renewable=True, is_active=True)

    expected_meter_reading = 100.5
    # collected date should be within x days prior to the previous quarter's end date
    expected_collected_at = datetime(2025, 3, 28, tzinfo=dt.timezone.utc)

    FormsetClass = setup_formset_class()
    formset = FormsetClass(
        queryset=Renewable.objects.none(),
        data={
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-delivery_point": dp1.id,
            "form-0-meter_reading": expected_meter_reading,
            "form-0-collected_at": expected_collected_at,
            "form-1-delivery_point": dp2.id,
            "has_confirmed_information_accuracy": "on",
            # form-1 is incomplete (no meter_reading or collected_at)
        },
    )

    assert Renewable.objects.count() == 0
    assert formset.is_valid()
    instances = formset.save()
    assert len(instances) == 1
    assert Renewable.objects.count() == 1
    assert instances[0].meter_reading == expected_meter_reading


@pytest.mark.django_db
def test_renewable_formset_save_without_commit(monkeypatch):
    """Test save() method of RenewableFormset with commit=False."""
    # current_tz = timezone.get_current_timezone()
    now = datetime(2025, 5, 6, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(timezone, "now", lambda: now)

    dp1 = DeliveryPointFactory(has_renewable=True, is_active=True)
    expected_meter_reading = 100.5
    # collected date should be within x days prior to the previous quarter's end date
    expected_collected_at = datetime(2025, 3, 28, tzinfo=dt.timezone.utc)

    FormsetClass = setup_formset_class()
    formset = FormsetClass(
        queryset=Renewable.objects.none(),
        data={
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-delivery_point": dp1.id,
            "form-0-meter_reading": expected_meter_reading,
            "form-0-collected_at": expected_collected_at,
            "has_confirmed_information_accuracy": "on",
        },
    )

    assert formset.is_valid()
    instances = formset.save(commit=False)
    assert len(instances) == 1
    assert Renewable.objects.count() == 0  # nothing should be saved
    assert isinstance(instances[0], Renewable)
    assert instances[0].meter_reading == expected_meter_reading


@pytest.mark.django_db
def test_empty_renewable_formset_save(monkeypatch):
    """Test save() method of RenewableFormset with empty data."""
    FormsetClass = setup_formset_class()
    formset = FormsetClass(
        queryset=Renewable.objects.none(),
        data={
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "has_confirmed_information_accuracy": "on",
        },
    )

    assert formset.is_valid()
    instances = formset.save()
    assert len(instances) == 0
    assert Renewable.objects.count() == 0
