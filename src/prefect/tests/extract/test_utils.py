"""QualiCharge prefect indicators tests: extract.utils."""

from datetime import date, datetime

import pandas as pd
from pandas import NamedAgg

from indicators.extract import e5, utils
from indicators.models import IndicatorPeriod, Level
from indicators.types import Environment

DATE = datetime(2025, 1, 1)
SATURATION_RATIO = 0.1
OVERLOAD_RATIO = 0.2


def test_get_pdc_station_for_day():
    """Test the `get_pdc_station_for_day` function."""
    e5.e5(
        Environment.TEST,
        [Level.NATIONAL],
        start=DATE + IndicatorPeriod.DAY.duration,
        period=IndicatorPeriod.DAY.value,
        persist=True,
    )
    poc_station = utils.get_pdc_station_for_day(DATE, Environment.TEST)
    assert not poc_station.empty
    assert set(poc_station.columns) == {
        "latitude",
        "longitude",
        "puissance_nominale",
        "id_pdc_itinerance",
        "id_station_itinerance",
    }


def test_to_sampled_sessions() -> None:
    """Test to_sampled_sessions function."""
    samples_per_day = 24
    timestamp = pd.Timestamp("2025-04-25T00:00:00+02:00")
    start = [1, 1.2, 3, 5.5, 9, 13.1, 20]
    end = [2.1, 2.7, 5, 7.5, 12.1, 15.1, 22.6]

    test = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(hours=val) for val in start],
            "end": [timestamp + pd.Timedelta(hours=val) for val in end],
            "id_pdc_itinerance": ["p1", "p2", "p2", "p1", "p2", "p1", "p2"],
        }
    )
    pdc = test["id_pdc_itinerance"].unique()
    init = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(days=-1)] * len(pdc),
            "end": [timestamp + pd.Timedelta(hours=-1)] * len(pdc),
            "id_pdc_itinerance": pdc,
        }
    )
    res = utils.to_sampled_sessions(test, init, timestamp, samples_per_day)

    assert res.iloc[5]["occupation_pdc"] == "f_libre"
    assert res.iloc[6]["occupation_pdc"] == "occupe"


def test_to_sampled_statuses() -> None:
    """Test to_sampled_statuses function."""
    samples_per_day = 24
    timestamp = pd.Timestamp("2025-04-25T00:00:00+02:00")
    valeurs = [1, 1.2, 3, 3.5, 5, 6.1, 12]

    test = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(hours=val) for val in valeurs],
            "etat_pdc": [
                "en_service",
                "hors_service",
                "en_service",
                "en_service",
                "hors_service",
                "en_service",
                "hors_service",
            ],
            "id_pdc_itinerance": ["p1", "p2", "p2", "p1", "p2", "p1", "p2"],
        }
    )
    pdc = test["id_pdc_itinerance"].unique()
    init = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=-1)] * len(pdc),
            "etat_pdc": ["en_service"] * len(pdc),
            "id_pdc_itinerance": pdc,
        }
    )
    res = utils.to_sampled_statuses(test, init, timestamp, samples_per_day)

    assert res.iloc[25]["etat_pdc"] == "en_service"
    assert res.iloc[26]["etat_pdc"] == "hors_service"


def test_to_sampled_state_poc_and_to_state_poc_d() -> None:
    """Test to_sampled_state_poc and to_state_poc_d functions."""
    samples_per_day = 3
    sessions = pd.DataFrame(
        {
            "id_pdc_itinerance": ["p1", "p1", "p1", "p2", "p2", "p2", "p3", "p3", "p3"],
            "periode": [0, 1, 2, 0, 1, 2, 0, 1, 2],
            "occupation_pdc": [
                "occupe",
                "f_libre",
                "occupe",
                "f_libre",
                "occupe",
                "f_libre",
                "f_libre",
                "occupe",
                "f_libre",
            ],
        }
    )
    statuses = pd.DataFrame(
        {
            "id_pdc_itinerance": ["p1", "p1", "p1", "p3", "p3", "p3", "p4", "p4", "p4"],
            "periode": [0, 1, 2, 0, 1, 2, 0, 1, 2],
            "etat_pdc": [
                "hors_service",
                "hors_service",
                "en_service",
                "en_service",
                "hors_service",
                "hors_service",
                "en_service",
                "hors_service",
                "en_service",
            ],
        }
    )
    merged = utils.to_sampled_state_poc(sessions, statuses)
    assert list(merged["state"][0:4]) == ["occupe", "hors_service", "occupe", "libre"]

    merged_d = utils.to_state_poc_d(merged, samples_per_day)
    assert list(merged_d["id_pdc_itinerance"]) == ["p1", "p2", "p3", "p4"]
    assert list(merged_d["occupe"]) == [960.0, 480.0, 480.0, 0.0]
    assert list(merged_d["hors_service"]) == [480.0, 0.0, 480.0, 480.0]
    assert list(merged_d["libre"]) == [0.0, 960.0, 480.0, 960.0]


def test_to_sampled_state_grp_and_to_state_grp_h() -> None:
    """Test to_sampled_state_grp and to_state_grp_h functions."""
    test = pd.DataFrame(
        {
            "id_pdc_itinerance": ["p1", "p1", "p1", "p2", "p2", "p2", "p3", "p3", "p3"],
            "periode": [0, 1, 2, 0, 1, 2, 0, 1, 2],
            "state": [
                "occupe",
                "hors_service",
                "occupe",
                "libre",
                "occupe",
                "libre",
                "libre",
                "occupe",
                "hors_service",
            ],
        }
    )
    stations = pd.DataFrame(
        {
            "id_pdc_itinerance": ["p1", "p2", "p3"],
            "id_station_itinerance": ["s1", "s1", "s2"],
        }
    )
    state_grp = utils.to_sampled_state_grp(
        test, stations, "id_station_itinerance", SATURATION_RATIO, OVERLOAD_RATIO
    )
    assert list(state_grp["state"]) == [3, 5, 3, 2, 5, 1]
    assert list(state_grp["surcharge"]) == [False] * 6
    assert list(state_grp["sature"]) == [False, True, False] * 2
    assert list(state_grp["hs"]) == [False] * 5 + [True]
    assert list(state_grp["actif"]) == [True, False, True, False, False, False]
    assert list(state_grp["inactif"]) == [False, False, False, True, False, False]

    test = pd.DataFrame(
        {
            "id_pdc_itinerance": [
                "p1",
                "p1",
                "p1",
                "p1",
                "p1",
                "p1",
                "p2",
                "p2",
                "p2",
                "p2",
                "p2",
                "p2",
            ],
            "periode": [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5],
            "state": [
                "occupe",
                "hors_service",
                "occupe",
                "occupe",
                "hors_service",
                "libre",
                "libre",
                "libre",
                "occupe",
                "hors_service",
                "hors_service",
                "libre",
            ],
        }
    )
    stations = pd.DataFrame(
        {"id_pdc_itinerance": ["p1", "p2"], "id_station_itinerance": ["s1", "s1"]}
    )
    state_grp = utils.to_sampled_state_grp(
        test, stations, "id_station_itinerance", SATURATION_RATIO, OVERLOAD_RATIO
    )
    assert list(state_grp["state"]) == [3, 2, 5, 5, 1, 2]

    samples_per_day = 144
    intervals = 24 * 60 / samples_per_day
    state_grp["periode"] = pd.Timestamp(
        "2025-01-20 15:00:00", tz="UTC"
    ) + pd.to_timedelta(state_grp["periode"] * 10, unit="min")
    state_grp_h = utils.to_state_grp_h(
        state_grp,
        "id_station_itinerance",
        samples_per_day=samples_per_day,
        duree_etat_min=75,
    )
    assert state_grp_h["hs"][0] == intervals
    assert state_grp_h["inactif"][0] == intervals * 2
    assert state_grp_h["sature"][0] == intervals * 2
    assert state_grp_h["surcharge"][0] == 0
    assert state_grp_h["actif"][0] == intervals


def test_to_state_grp_d() -> None:
    """Test to_state_grp_d function."""
    state_grp_test = pd.DataFrame(
        {
            "id_station_itinerance": ["s1", "s1"],
            "periode": date(2026, 1, 15),
            "periode_h": [1, 2],
            "nb_pdc": 2,
            "hs": [10, 15],
            "inactif": [20, 30],
            "sature": [20, 10],
            "surcharge": [0, 5],
            "actif": [10, 15],
            "sature_h": [False, True],
            "surcharge_h": [True, True],
        }
    )
    grouped = state_grp_test.groupby(["id_station_itinerance", "periode"])
    grouped.agg(
        nb_pdc=NamedAgg("nb_pdc", "max"),
        nb_h=NamedAgg("periode", "count"),
        hs=NamedAgg("hs", "sum"),
        inactif=NamedAgg("inactif", "sum"),
        sature_cum=NamedAgg("sature", "sum"),
        sature_max=NamedAgg("sature", "max"),
        surcharge=NamedAgg("surcharge", "sum"),
        actif=NamedAgg("actif", "sum"),
    ).reset_index()

    state_grp_d = utils.to_state_grp_d(state_grp_test, "id_station_itinerance")
    assert state_grp_d["id_station_itinerance"][0] == "s1"
    assert state_grp_d["periode"][0] == date(2026, 1, 15)
    assert state_grp_d["nb_pdc"][0] == 2 * 1
    assert state_grp_d["nb_h"][0] == 2 * 1
    assert state_grp_d["hs"][0] == 25 * 1
    assert state_grp_d["inactif"][0] == 50 * 1
    assert state_grp_d["sature_cum"][0] == 30 * 1
    assert state_grp_d["sature_max"][0] == 20 * 1
    assert state_grp_d["surcharge"][0] == 5 * 1
    assert state_grp_d["actif"][0] == 25 * 1
