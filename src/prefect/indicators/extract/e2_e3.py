"""QualiCharge prefect indicators: state historicization.

E2: daily states of charge points in activity.
E3: daily states of stations in activity.
E6: daily states of pools.
"""

import os
from datetime import date, datetime, timedelta

import pandas as pd
from pandas import NamedAgg
from prefect import flow, runtime, task
from prefect.cache_policies import NONE
from prefect.futures import wait

from indicators.extract.utils import (
    filter_sessions_duration,
    get_pdc_station_for_day,
    to_sampled_sessions,
    to_sampled_state_grp,
    to_sampled_state_poc,
    to_sampled_statuses,
    to_state_grp,
    to_state_poc,
)
from indicators.models import IndicatorPeriod, Level
from indicators.types import Environment
from indicators.utils import (
    export_indicators,
    get_period_start_from_pit,
)

HISTORY_STRATEGY_FIELD: str = "mean"
PERIOD = IndicatorPeriod.DAY
CHUNK_SIZE: int = 200
SAMPLES: int = 288  # 5 min
SATURE_H: int = 45  # minimum duration (min) of saturation to have a saturated hour

ID_POC: str = "id_pdc_itinerance"
ID_STATION: str = "id_station_itinerance"
SATURATION_RATIO = 0.1
OVERLOAD_RATIO = 0.2
MAX_SESSION_DURATION_HOURS: float = 10


@task(task_run_name="read-S3-{bucket}-{day:%y-%m-%d}", cache_policy=NONE)
def read_s3_data(day: date, environment: str, bucket: str) -> pd.DataFrame:
    """Read S3 data for state historicization."""
    dir_path = f"{bucket}/{day.year}/{day.month}/{day.day}"
    file_path = f"{dir_path}/{environment}.parquet"
    s3_path = f"s3://{file_path}"
    s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", "")
    df = pd.read_parquet(
        s3_path,
        engine="pyarrow",
        dtype_backend="pyarrow",
        storage_options={"endpoint_url": s3_endpoint_url},
    )  # type: ignore[call-overload]
    return df


def read_statics(day: date, environment: Environment, min_power: float) -> pd.DataFrame:
    """Read static data for POC and stations."""
    statics = get_pdc_station_for_day(day, environment)
    statics["unite"] = statics["id_pdc_itinerance"].str[:5]
    return statics[statics["puissance_nominale"] >= min_power]


def filter_statuses_sessions(
    sessions: pd.DataFrame, statuses: pd.DataFrame, statics: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter statuses and sessions with statics data."""
    sessions = sessions[sessions[ID_POC].isin(statics[ID_POC])].copy()
    active_poc = sessions[ID_POC].unique()
    statuses = statuses[statuses[ID_POC].isin(active_poc)].copy()
    return (statuses, sessions)


def get_sampled_state_poc(
    day: date,
    samples_per_day: int,
    sessions: pd.DataFrame,
    statuses: pd.DataFrame,
) -> pd.DataFrame:
    """Extract complete POC with sessions and statuses."""
    min_duration = timedelta(minutes=24 * 60 / samples_per_day)
    timestamp = pd.Timestamp(day.isoformat() + "T00:00:00+00:00")
    pocs_with_sessions = pd.Series(sessions[ID_POC].unique())
    pocs_with_statuses = pd.Series(statuses[ID_POC].unique())
    all_pocs = (
        pd.concat([pocs_with_sessions, pocs_with_statuses])
        .drop_duplicates()
        .reset_index(drop=True)
    )

    attributes_statuses = [ID_POC, "horodatage", "etat_pdc", "occupation_pdc"]
    statuses = statuses[attributes_statuses].copy()
    statuses["horodatage"] = statuses["horodatage"].astype("datetime64[s, UTC]")

    attributes_sessions = [ID_POC, "start", "end"]
    sessions = sessions[attributes_sessions].copy()
    sessions["start"] = sessions["start"].astype("datetime64[s, UTC]")
    sessions["end"] = sessions["end"].astype("datetime64[s, UTC]")

    init_start_statuses = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=-1)] * len(all_pocs),
            "etat_pdc": ["en_service"] * len(all_pocs),
            "occupation_pdc": ["libre"] * len(all_pocs),
            "id_pdc_itinerance": all_pocs,
        }
    )
    init_end_statuses = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=1)] * len(all_pocs),
            "etat_pdc": ["en_service"] * len(all_pocs),
            "occupation_pdc": ["libre"] * len(all_pocs),
            "id_pdc_itinerance": all_pocs,
        }
    )
    init_statuses = pd.concat([init_start_statuses, init_end_statuses])
    init_statuses["horodatage"] = pd.to_datetime(init_statuses["horodatage"], utc=True)
    sampled_statuses = to_sampled_statuses(
        statuses, init_statuses, timestamp, samples_per_day, min_duration=min_duration
    )

    init_sessions = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(hours=-2)] * len(all_pocs),
            "end": [timestamp + pd.Timedelta(hours=-1)] * len(all_pocs),
            "id_pdc_itinerance": all_pocs,
        }
    )
    sampled_sessions = to_sampled_sessions(
        sessions,
        init_sessions,
        timestamp,
        samples_per_day,
    )

    return to_sampled_state_poc(sampled_sessions, sampled_statuses)


@task(task_run_name="sampled_chunk-{day:%y-%m-%d}", cache_policy=NONE)
def get_state_poc_for_chunk(
    day: date,
    samples_per_day: int,
    statics_chunk: pd.DataFrame,
    sessions: pd.DataFrame,
    statuses: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate state_poc for a chunk."""
    statuses_chunk, sessions_chunk = filter_statuses_sessions(
        sessions, statuses, statics_chunk
    )
    sampled_state_poc_chunk = get_sampled_state_poc(
        day,
        samples_per_day,
        sessions_chunk,
        statuses_chunk,
    )
    state_poc_chunk = to_state_poc(sampled_state_poc_chunk, samples_per_day)
    return (sampled_state_poc_chunk, state_poc_chunk)


def get_chunked_state_poc(  # noqa: PLR0913
    statics: pd.DataFrame,
    day: date,
    samples_per_day: int,
    chunk_size: int,
    sessions: pd.DataFrame,
    statuses: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate sampled_state_poc and state_poc in chunks."""
    chunks = [
        statics.iloc[i : i + chunk_size] for i in range(0, len(statics), chunk_size)
    ]
    futures = [
        get_state_poc_for_chunk.submit(
            day,
            samples_per_day,
            chunk,
            sessions,
            statuses,
        )  # type: ignore[call-overload]
        for chunk in chunks
    ]
    wait(futures)

    sampled_state_poc = pd.concat(
        [future.result()[0] for future in futures], ignore_index=True
    )
    state_poc = pd.concat([future.result()[1] for future in futures], ignore_index=True)
    return (sampled_state_poc, state_poc)


def get_chunked_state_grp(  # noqa: PLR0913
    statics: pd.DataFrame,
    sampled_state_poc: pd.DataFrame,
    chunk_size: int,
    id_grp: str,
    samples_per_day: int,
    saturation_ratio: float,
    overload_ratio: float,
    add_full_use: bool,
    add_latency: bool,
) -> pd.DataFrame:
    """Calculate state_grp in chunks."""
    codes, _ = pd.factorize(statics[id_grp])
    statics["chunk"] = codes // chunk_size
    chunks = statics.groupby("chunk")

    futures = [
        to_state_grp.submit(
            to_sampled_state_grp(
                sampled_state_poc[sampled_state_poc[ID_POC].isin(chunk[ID_POC])],
                chunk,
                id_grp,
                saturation_ratio,
                overload_ratio,
                add_full_use,
                add_latency,
            ),  # type: ignore[call-overload]
            id_grp,
            samples_per_day,
        )
        for _, chunk in chunks
    ]

    state_grp = pd.concat([future.result() for future in futures], ignore_index=True)
    return state_grp


@flow(flow_run_name="meta-e2-d")
def e2(  # noqa: PLR0913
    environment: Environment,
    state_poc: pd.DataFrame,
    sessions_poc: pd.DataFrame,
    day: date,
    create_artifact: bool,
    persist: bool,
) -> pd.DataFrame:
    """Run e2 subflow."""
    # state_poc = to_state_poc(sampled_state_poc, samples_per_day)
    full_state_poc = pd.merge(state_poc, sessions_poc, on=ID_POC, how="left").fillna(0)
    indicators_e2 = pd.DataFrame(
        {
            "target": "00",
            "value": len(full_state_poc),
            "code": "e2",
            "level": Level.NATIONAL,
            "period": PERIOD,
            "timestamp": day.isoformat(),
            "category": None,
            "extras": [
                {
                    "id_pdc_itinerance": list(full_state_poc[ID_POC]),
                    "occupe": list(full_state_poc["occupe"]),
                    "occupe_max": list(full_state_poc["occupe_max"]),
                    "hors_service": list(full_state_poc["hors_service"]),
                    "libre": list(full_state_poc["libre"]),
                    "pseudo_libre": list(full_state_poc["pseudo_libre"]),
                    "pseudo_occupe": list(full_state_poc["pseudo_occupe"]),
                    "sessions_nb": list(full_state_poc["sessions_nb"]),
                    "energy_cum": list(full_state_poc["energy_cum"]),
                }
            ],
        }
    )
    desc_e2 = f"e2 report at {day} (period: {PERIOD})"
    flow_name_e2 = "e2-" + runtime.flow_run.name
    export_indicators(
        indicators_e2, environment, flow_name_e2, desc_e2, create_artifact, persist
    )
    return indicators_e2


@flow(flow_run_name="meta-e3-d")
def e3(  # noqa: PLR0913
    environment: Environment,
    state_station: pd.DataFrame,
    info_sessions_stations: pd.DataFrame,
    day: date,
    create_artifact: bool,
    persist: bool,
) -> pd.DataFrame:
    """Run e3 subflow."""
    # state_station = to_state_grp(sampled_state_station, ID_STATION, SAMPLES)
    full_state_station = pd.merge(
        state_station, info_sessions_stations, on=ID_STATION, how="left"
    ).fillna(0)
    indicators_e3 = pd.DataFrame(
        {
            "target": "00",
            "value": len(full_state_station),
            "code": "e3",
            "level": Level.NATIONAL,
            "period": PERIOD,
            "timestamp": day.isoformat(),
            "category": None,
            "extras": [
                {
                    "id_station_itinerance": list(full_state_station[ID_STATION]),
                    "nb_pdc": list(full_state_station["nb_pdc"]),
                    "hs": list(full_state_station["hs"]),
                    "inactif": list(full_state_station["inactif"]),
                    "sature_cum": list(full_state_station["sature_cum"]),
                    "sature_max": list(full_state_station["sature_max"]),
                    "surcharge": list(full_state_station["surcharge"]),
                    "actif": list(full_state_station["actif"]),
                    "pu_cum": list(full_state_station["pu_cum"]),
                    "pu_max": list(full_state_station["pu_max"]),
                    "pu_len": list(full_state_station["pu_len"]),
                    "sessions_nb": list(full_state_station["sessions_nb"]),
                    "energy_cum": list(full_state_station["energy_cum"]),
                }
            ],
        }
    )

    desc_e3 = f"e3 report at {day} (period: {PERIOD})"
    flow_name_e3 = "e3-" + runtime.flow_run.name
    export_indicators(
        indicators_e3, environment, flow_name_e3, desc_e3, create_artifact, persist
    )
    return indicators_e3


@flow(flow_run_name="meta-e2e3-d")
def e2_e3(  # noqa: PLR0913
    environment: Environment,
    min_power: float,
    start: datetime | None = None,
    offset: int = -1,
    chunk_size: int = CHUNK_SIZE,
    samples_per_day: int = SAMPLES,
    create_artifact: bool = False,
    persist: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run all e2 and e3 subflows."""
    start = (
        datetime.now()
        if not offset and start is None
        else get_period_start_from_pit(start, offset, PERIOD)
    )
    # common to indicators e2 and e3
    day = start.date()
    min_duration = timedelta(minutes=24 * 60 / samples_per_day)
    max_duration = timedelta(hours=MAX_SESSION_DURATION_HOURS)

    statuses = read_s3_data(day, environment, "qualicharge-statuses")
    sessions_s3 = read_s3_data(day, environment, "qualicharge-sessions")
    sessions = filter_sessions_duration(
        sessions_s3, min_duration=min_duration, max_duration=max_duration
    )
    statics = read_statics(day, environment, min_power)
    sessions_poc = (
        sessions.groupby(ID_POC)
        .agg(
            sessions_nb=NamedAgg("energy", "count"),
            energy_cum=NamedAgg("energy", "sum"),
        )
        .reset_index()
    )
    sessions_stations = pd.merge(
        statics[[ID_POC, ID_STATION]], sessions_poc, on=ID_POC, how="left"
    ).fillna(0)
    info_sessions_stations = (
        sessions_stations[[ID_STATION, "sessions_nb", "energy_cum"]]
        .groupby(ID_STATION)
        .sum()
        .reset_index()
    )
    # e2 indicator
    sampled_state_poc, state_poc = get_chunked_state_poc(
        statics, day, samples_per_day, chunk_size, sessions, statuses
    )
    """chunks = [
        statics.iloc[i : i + chunk_size] for i in range(0, len(statics), chunk_size)
    ]
    futures = [
        get_sampled_state_poc_for_chunk.submit(
            day,
            samples_per_day,
            chunk,
            sessions,
            statuses,
        )  # type: ignore[call-overload]
        for chunk in chunks
    ]
    wait(futures)

    sampled_state_poc = pd.concat(
        [future.result() for future in futures], ignore_index=True
    )
    """
    indicators_e2 = e2(
        environment,
        state_poc,
        sessions_poc,
        day,
        create_artifact,
        persist,
    )
    # e3 indicator
    state_station = get_chunked_state_grp(
        statics,
        sampled_state_poc,
        chunk_size,
        ID_STATION,
        SAMPLES,
        SATURATION_RATIO,
        OVERLOAD_RATIO,
        add_full_use=True,
        add_latency=True,
    )

    """codes, _ = pd.factorize(statics[ID_STATION])
    statics["chunk"] = codes // chunk_size
    chunks_group = statics.groupby("chunk")

    futures = [
        to_sampled_state_grp.submit(
            sampled_state_poc[sampled_state_poc[ID_POC].isin(chunk[ID_POC])],
            chunk,
            ID_STATION,
            SATURATION_RATIO,
            OVERLOAD_RATIO,
            add_full_use=True,
            add_latency=True,
        )  # type: ignore[call-overload]
        for _, chunk in chunks_group
    ]
    wait(futures)

    sampled_state_station = pd.concat(
        [future.result() for future in futures], ignore_index=True
    )"""
    indicators_e3 = e3(
        environment,
        state_station,
        info_sessions_stations,
        day,
        create_artifact,
        persist,
    )
    return (indicators_e2, indicators_e3)
