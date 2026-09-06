"""QualiCharge prefect indicators tests: extract.utils."""

from datetime import datetime, timedelta

import pandas as pd
from pandas import NamedAgg

from indicators.extract import e5, utils
from indicators.models import IndicatorPeriod, Level
from indicators.types import Environment

DATE = datetime(2025, 1, 1)
SATURATION_RATIO = 0.1
OVERLOAD_RATIO = 0.2
LEN_RES = 48


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
    EXPECTED_LEN_SESSIONS = 72
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
    pdc = ["p1", "p2", "p3"]
    init = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(hours=-1)] * len(pdc),
            "end": [timestamp + pd.Timedelta(hours=0.5)] * len(pdc),
            "id_pdc_itinerance": pdc,
        }
    )
    sessions = utils.to_sampled_sessions(
        utils.filter_sessions_duration(test), init, timestamp, samples_per_day
    )

    assert len(sessions) == EXPECTED_LEN_SESSIONS
    assert sessions.iloc[0]["occupation_pdc"] == "occupe"
    assert sessions.iloc[1]["occupation_pdc"] == "occupe"
    assert sessions.iloc[5]["occupation_pdc"] == "f_libre"
    assert sessions.iloc[6]["occupation_pdc"] == "occupe"
    assert sessions.iloc[34]["occupation_pdc"] == "occupe"

    res_min = utils.to_sampled_sessions(
        utils.filter_sessions_duration(test, min_duration=timedelta(hours=1.2)),
        init,
        timestamp,
        samples_per_day,
    )
    assert res_min.iloc[1]["occupation_pdc"] == "f_libre"

    res_max = utils.to_sampled_sessions(
        utils.filter_sessions_duration(test, max_duration=timedelta(hours=3)),
        init,
        timestamp,
        samples_per_day,
    )
    assert res_max.iloc[34]["occupation_pdc"] == "f_libre"

    end = [6.1, 2.7, 5, 7.5, 12.1, 15.1, 22.6]
    test2 = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(hours=val) for val in start],
            "end": [timestamp + pd.Timedelta(hours=val) for val in end],
            "id_pdc_itinerance": ["p1", "p2", "p2", "p1", "p2", "p1", "p2"],
        }
    )
    pdc2 = test2["id_pdc_itinerance"].unique()
    init2 = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(hours=-1)] * len(pdc2),
            "end": [timestamp + pd.Timedelta(hours=0.5)] * len(pdc2),
            "id_pdc_itinerance": pdc2,
        }
    )
    sessions = utils.to_sampled_sessions(
        utils.filter_sessions_duration(test2), init2, timestamp, samples_per_day
    )

    assert sessions.iloc[5]["occupation_pdc"] == "occupe"
    assert sessions.iloc[6]["occupation_pdc"] == "occupe"


def _make_status_init_data(timestamp: pd.Timestamp, pdcs: list) -> pd.DataFrame:
    init_start = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=-1)] * len(pdcs),
            "etat_pdc": ["en_service"] * len(pdcs),
            "occupation_pdc": ["libre"] * len(pdcs),
            "id_pdc_itinerance": pdcs,
        }
    )
    init_end = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=1)] * len(pdcs),
            "etat_pdc": ["en_service"] * len(pdcs),
            "occupation_pdc": ["libre"] * len(pdcs),
            "id_pdc_itinerance": pdcs,
        }
    )
    return pd.concat([init_start, init_end])


def test_to_sampled_statuses() -> None:
    """Test to_sampled_statuses function."""
    samples_per_day = 24
    timestamp = pd.Timestamp("2025-04-25T00:00:00+02:00")
    values = [1, 1.2, 3, 3.5, 5, 6.1, 12]

    # test 1 : different number of pdcs
    EXPECTED_LEN_STATUSES_1 = 72
    test = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(hours=val) for val in values],
            "etat_pdc": [
                "en_service",
                "hors_service",
                "en_service",
                "en_service",
                "hors_service",
                "en_service",
                "hors_service",
            ],
            "occupation_pdc": [
                "occupe",
                "libre",
                "libre",
                "occupe",
                "occupe",
                "libre",
                "libre",
            ],
            "id_pdc_itinerance": ["p1", "p2", "p2", "p1", "p2", "p1", "p2"],
        }
    )
    init = _make_status_init_data(timestamp, ["p1", "p2", "p3"])
    statuses = utils.to_sampled_statuses(test, init, timestamp, samples_per_day)
    assert len(statuses) == EXPECTED_LEN_STATUSES_1
    assert statuses.iloc[25]["etat_pdc"] == "en_service"
    assert statuses.iloc[26]["etat_pdc"] == "hors_service"

    statuses = utils.to_sampled_statuses(
        test, init, timestamp, samples_per_day, timedelta(hours=1.9)
    )
    assert len(statuses) == EXPECTED_LEN_STATUSES_1
    assert statuses.iloc[25]["etat_pdc"] == "en_service"
    assert statuses.iloc[26]["etat_pdc"] == "en_service"

    # test 2 : exact number of pdcs
    EXPECTED_LEN_STATUSES_2 = 48
    init = _make_status_init_data(timestamp, list(test["id_pdc_itinerance"].unique()))
    statuses = utils.to_sampled_statuses(test, init, timestamp, samples_per_day)
    assert len(statuses) == EXPECTED_LEN_STATUSES_2
    assert statuses.iloc[25]["etat_pdc"] == "en_service"
    assert statuses.iloc[26]["etat_pdc"] == "hors_service"
    statuses = utils.to_sampled_statuses(
        test, init, timestamp, samples_per_day, timedelta(hours=1.9)
    )
    assert len(statuses) == EXPECTED_LEN_STATUSES_2
    assert statuses.iloc[25]["etat_pdc"] == "en_service"
    assert statuses.iloc[26]["etat_pdc"] == "en_service"

    # test 3 : 'inconnu' value
    EXPECTED_LEN_STATUSES_3 = 48
    test = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(hours=val) for val in values],
            "etat_pdc": [
                "en_service",
                "hors_service",
                "inconnu",
                "en_service",
                "hors_service",
                "en_service",
                "hors_service",
            ],
            "occupation_pdc": [
                "occupe",
                "libre",
                "inconnu",
                "occupe",
                "occupe",
                "libre",
                "libre",
            ],
            "id_pdc_itinerance": ["p1", "p2", "p2", "p1", "p2", "p1", "p2"],
        }
    )
    init = _make_status_init_data(timestamp, list(test["id_pdc_itinerance"].unique()))
    statuses = utils.to_sampled_statuses(test, init, timestamp, samples_per_day)
    assert len(statuses) == EXPECTED_LEN_STATUSES_3
    assert statuses.iloc[25]["etat_pdc"] == "en_service"
    assert statuses.iloc[26]["etat_pdc"] == "hors_service"
    statuses = utils.to_sampled_statuses(
        test, init, timestamp, samples_per_day, timedelta(hours=1.9)
    )
    assert len(statuses) == EXPECTED_LEN_STATUSES_3
    assert statuses.iloc[25]["etat_pdc"] == "en_service"
    assert statuses.iloc[26]["etat_pdc"] == "hors_service"

    # test 4 : min_duration
    timestamp = pd.Timestamp("2026-07-14T00:00:00+02:00")
    samples_per_day = 288
    min_duration = timedelta(minutes=24 * 60 / samples_per_day)

    init_statuses = _make_status_init_data(timestamp, ["p1", "p2"])
    values = [10.45, 10.5]
    statuses = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(hours=val) for val in values],
            "etat_pdc": ["hors_service", "en_service"],
            "occupation_pdc": ["inconnu", "libre"],
            "id_pdc_itinerance": ["p1", "p1"],
        }
    )
    sampled_statuses = utils.to_sampled_statuses(
        statuses, init_statuses, timestamp, samples_per_day, min_duration=min_duration
    )
    assert sampled_statuses["etat_pdc"].eq("en_service").all()
    assert sampled_statuses["occupation_pdc"].eq("libre").all()


def test_to_sampled_state_poc_and_to_state_poc() -> None:
    """Test to_sampled_state_poc and to_state_poc functions."""
    samples_per_day = 24
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
                "occupe",
            ],
        }
    )
    status = pd.DataFrame(
        {
            "id_pdc_itinerance": ["p1", "p1", "p1", "p2", "p2", "p2", "p3", "p3", "p3"],
            "periode": [0, 1, 2, 0, 1, 2, 0, 1, 2],
            "occupation_pdc": [
                "occupe",
                "libre",
                "occupe",
                "libre",
                "occupe",
                "libre",
                "libre",
                "occupe",
                "occupe",
            ],
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

    merged = utils.to_sampled_state_poc(sessions, status)
    assert merged["pseudo_libre"].eq(pd.Series([False] * 9)).all()
    assert merged["pseudo_occupe"].eq(pd.Series([False] * 9)).all()

    status["id_pdc_itinerance"] = ["p1", "p1", "p1", "p3", "p3", "p3", "p4", "p4", "p4"]
    merged = utils.to_sampled_state_poc(sessions, status)
    assert merged["pseudo_libre"].sum() == 1
    assert merged["pseudo_occupe"].sum() == 1

    status["id_pdc_itinerance"] = ["p1", "p1", "p1", "p2", "p2", "p2", "p3", "p3", "p3"]
    sessions.loc[2, "occupation_pdc"] = "f_libre"
    merged = utils.to_sampled_state_poc(sessions, status)
    assert merged["pseudo_libre"].sum() == 0
    assert merged["pseudo_occupe"].sum() == 1

    sessions.loc[2, "occupation_pdc"] = "occupe"
    sessions.loc[3, "occupation_pdc"] = "occupe"
    merged = utils.to_sampled_state_poc(sessions, status)
    assert merged["pseudo_libre"].sum() == 1
    assert merged["pseudo_occupe"].sum() == 0

    state_d = utils.to_state_poc(merged, samples_per_day)
    assert list(state_d.iloc[0].values) == ["p1", 120.0, 60.0, 60.0, 0.0, 0.0, 0.0]
    assert list(state_d.iloc[1].values) == ["p2", 120.0, 60.0, 60.0, 0.0, 60.0, 0.0]
    assert list(state_d.iloc[2].values) == ["p3", 120.0, 60.0, 0.0, 60.0, 0.0, 0.0]


def test_to_sampled_state_grp_and_to_state_grp() -> None:
    """Test to_sampled_state_grp and to_state_grp functions."""
    EXPECTED_MAX_DURATION = 60.0
    SATURATION_RATIO_MIN = 0.01
    timestamp = pd.Timestamp("2025-04-25T00:00:00+02:00")
    # test 1 : multi-stations
    test = pd.DataFrame(
        {
            "id_pdc_itinerance": ["p1", "p1", "p1", "p2", "p2", "p2", "p3", "p3", "p3"],
            "periode": [
                timestamp + pd.Timedelta(hours=val)
                for val in [0, 1, 2, 0, 1, 2, 0, 1, 2]
            ],
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
            "pseudo_libre": [
                False,
                False,
                False,
                False,
                False,
                False,
                True,
                False,
                False,
            ],
            "pseudo_occupe": [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                True,
                False,
            ],
        }
    )
    stations = pd.DataFrame(
        {
            "id_pdc_itinerance": ["p1", "p2", "p3"],
            "id_station_itinerance": ["s1", "s1", "s2"],
        }
    )
    sampled_state_station = utils.to_sampled_state_grp(
        test,
        stations,
        "id_station_itinerance",
        SATURATION_RATIO,
        OVERLOAD_RATIO,
        add_full_use=True,
        add_latency=True,
    )
    assert list(sampled_state_station["state"]) == [3, 5, 3, 2, 5, 1]
    assert list(sampled_state_station["surcharge"]) == [False] * 6
    assert list(sampled_state_station["sature"]) == [False, True, False] * 2
    assert list(sampled_state_station["hs"]) == [False] * 5 + [True]
    assert list(sampled_state_station["actif"]) == [
        True,
        False,
        True,
        False,
        False,
        False,
    ]
    assert list(sampled_state_station["inactif"]) == [
        False,
        False,
        False,
        True,
        False,
        False,
    ]

    hourly_max_pu = utils.hourly_maximum(
        sampled_state_station, "id_station_itinerance", "periode", "pu", 12
    )
    assert list(hourly_max_pu["index_state_grp"]) == [2, 5]
    assert list(hourly_max_pu["pu_max"]) == [3.0, 2.0]

    max_duration = utils.maxi_duration(
        sampled_state_station, "id_station_itinerance", "periode", "pu"
    )
    assert list(max_duration["first"]) == [
        pd.Timestamp("2025-04-25 00:00:00+02:00"),
        pd.Timestamp("2025-04-25 01:00:00+02:00"),
    ]
    assert list(max_duration["duration"]) == [3, 2]

    # test 2 : mono-station
    test = pd.DataFrame(
        {
            "id_pdc_itinerance": [
                "p1",
                "p1",
                "p1",
                "p1",
                "p2",
                "p2",
                "p2",
                "p2",
                "p3",
                "p3",
                "p3",
                "p3",
                "p4",
                "p4",
                "p4",
                "p4",
                "p5",
                "p5",
                "p5",
                "p5",
                "p6",
                "p6",
                "p6",
                "p3",
            ],
            "periode": [
                timestamp + pd.Timedelta(hours=val) for val in [0, 1, 2, 3] * 6
            ],
            # 'periode' : timestamp,
            "state": ["libre", "occupe", "occupe", "occupe"] * 6,
            "pseudo_libre": [True, True, False, False] * 6,
            "pseudo_occupe": [False, True, True, False] * 6,
        }
    )
    stations = pd.DataFrame(
        {
            "id_pdc_itinerance": ["p1", "p2", "p3", "p4", "p5", "p6"],
            "id_station_itinerance": ["s1"] * 6,
        }
    )
    res = utils.to_sampled_state_grp(test, stations, "id_station_itinerance", 0.01, 0.2)
    assert res["sature"][3]
    res = utils.to_sampled_state_grp(
        test,
        stations,
        "id_station_itinerance",
        SATURATION_RATIO_MIN,
        OVERLOAD_RATIO,
        add_full_use=True,
        add_latency=True,
    )
    assert (res["sature"] == res["pu"]).all()
    test.loc[2, "state"] = "libre"
    test.loc[3, "state"] = "libre"
    res = utils.to_sampled_state_grp(
        test,
        stations,
        "id_station_itinerance",
        SATURATION_RATIO_MIN,
        OVERLOAD_RATIO,
        add_full_use=True,
        add_latency=True,
    )
    assert not res["sature"][2]
    assert res["pu"][2]
    assert res["pu"][3]
    test.loc[6, "state"] = "libre"
    test.loc[7, "state"] = "libre"
    res = utils.to_sampled_state_grp(
        test,
        stations,
        "id_station_itinerance",
        SATURATION_RATIO_MIN,
        OVERLOAD_RATIO,
        add_full_use=True,
        add_latency=True,
    )
    assert res["pu"][2]
    assert not res["pu"][3]

    res_d = utils.to_state_grp(res, "id_station_itinerance", 24)
    assert res_d["pu_max"].values[0] == EXPECTED_MAX_DURATION
    assert res_d["sature_max"].values[0] == EXPECTED_MAX_DURATION
    assert list(
        res_d[["hs", "inactif", "pu_cum", "sature_cum", "surcharge", "actif"]].values[0]
    ) == list(
        (
            res[["hs", "inactif", "pu", "sature", "surcharge", "actif"]].sum() * 60.0
        ).values
    )


def test_hysteresis() -> None:
    """Test hysteresis function."""
    serie = pd.Series([1, 2, 5, 7, 5, 8, 10, 12, 8, 11, 8, 5, 7, 2])
    res = utils.hysteresis(serie, 6, 9)
    assert res[6:10].all()
    assert not res[:5].all()


def test_maxi_duration() -> None:
    """Test maxi_duration function."""
    timestamp = pd.Timestamp("2025-04-25T00:00:00+02:00")
    periodes = [1, 2, 3, 4, 5, 6, 7, 8, 9] * 2

    df = pd.DataFrame(
        {
            "occupe": [
                False,
                True,
                True,
                False,
                True,
                True,
                True,
                False,
                True,
                False,
                True,
                True,
                True,
                True,
                False,
                True,
                False,
                True,
            ],
            "station": ["s1"] * 9 + ["s2"] * 9,
            "periode": [timestamp + pd.Timedelta(hours=per) for per in periodes],
        }
    )

    pu_duration = utils.maxi_duration(df, "station", "periode", "occupe")
    assert list(pu_duration["duration"]) == [3, 4]

    df["occupe"] = [False, True, False, True, False, True, False, True, False] + [
        False
    ] * 9
    pu_duration = utils.maxi_duration(df, "station", "periode", "occupe")
    assert pu_duration["duration"].iloc[0] == 1
    assert len(pu_duration) == 1


def test_adding_energy_and_number_of_sessions() -> None:
    """Test adding_energy and number of sessions."""
    EXPECTED_SESSIONS_NB = 4
    EXPECTED_ENERGY = 170.0
    start = [1, 1.2, 3, 5.5, 9, 13.1, 20]
    end = [2.1, 2.7, 5, 7.5, 12.1, 15.1, 22.6]
    timestamp = pd.Timestamp("2025-04-25T00:00:00+02:00")

    sessions = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(hours=val) for val in start],
            "end": [timestamp + pd.Timedelta(hours=val) for val in end],
            "id_pdc_itinerance": ["p1", "p2", "p2", "p1", "p2", "p1", "p2"],
            "energy": [10, 20, 30, 40, 50, 60, 70],
        }
    )
    states = pd.DataFrame(
        {
            "id_pdc_itinerance": ["p0", "p2", "p3"],
            "libre": [10, 20, 30],
            "occupe": [5, 10, 15],
        }
    )
    infos_poc = (
        sessions.groupby("id_pdc_itinerance")
        .agg(
            sessions_nb=NamedAgg("energy", "count"),
            energy_cum=NamedAgg("energy", "sum"),
        )
        .reset_index()
    )

    full_states = pd.merge(
        states, infos_poc, on="id_pdc_itinerance", how="left"
    ).fillna(0)

    assert (
        full_states.loc[full_states["id_pdc_itinerance"] == "p2", "sessions_nb"].values[
            0
        ]
        == EXPECTED_SESSIONS_NB
    )
    assert (
        full_states.loc[full_states["id_pdc_itinerance"] == "p2", "energy_cum"].values[
            0
        ]
        == EXPECTED_ENERGY
    )
