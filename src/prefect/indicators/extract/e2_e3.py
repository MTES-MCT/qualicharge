"""QualiCharge prefect indicators: state historicization.

E2: daily states of charge points in activity.
E3: daily states of stations in activity.
"""

import os
from datetime import date, datetime

import pandas as pd
from prefect import flow, runtime, task
from prefect.cache_policies import NONE
from prefect.futures import wait

from indicators.extract.utils import (
    get_pdc_station_for_day,
    to_sampled_sessions,
    to_sampled_state_grp,
    to_sampled_state_poc,
    to_sampled_statuses,
    to_state_grp_d,
    to_state_grp_h,
    to_state_poc_d,
)
from indicators.models import IndicatorPeriod, Level
from indicators.types import Environment
from indicators.utils import (
    export_indicators,
    get_period_start_from_pit,
)

HISTORY_STRATEGY_FIELD: str = "mean"
PERIOD = IndicatorPeriod.DAY
CHUNK_SIZE: int = 2000
SAMPLES: int = 288  # 5 min
SATURE_H: int = 45  # minimum duration (min) of saturation to have a saturated hour

ID_POC: str = "id_pdc_itinerance"
ID_STATION: str = "id_station_itinerance"
SATURATION_RATIO = 0.1
OVERLOAD_RATIO = 0.2


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
    timestamp = pd.Timestamp(day.isoformat() + "T00:00:00+00:00")
    pocs_with_sessions = sessions[ID_POC].unique()
    pocs_with_statuses = statuses[ID_POC].unique()

    attributes_statuses = [ID_POC, "horodatage", "etat_pdc"]
    statuses = statuses[attributes_statuses]

    attributes_sessions = [ID_POC, "start", "end"]
    sessions = sessions[attributes_sessions]
    sessions["start"] = sessions["start"].astype("datetime64[s, UTC]")
    sessions["end"] = sessions["end"].astype("datetime64[s, UTC]")

    init_statuses = pd.DataFrame(
        {
            "horodatage": [timestamp + pd.Timedelta(days=-1)] * len(pocs_with_statuses),
            "etat_pdc": ["en_service"] * len(pocs_with_statuses),
            "id_pdc_itinerance": pocs_with_statuses,
        }
    )
    sampled_statuses = to_sampled_statuses(
        statuses, init_statuses, timestamp, samples_per_day
    )

    init_sessions = pd.DataFrame(
        {
            "start": [timestamp + pd.Timedelta(days=-1)] * len(pocs_with_sessions),
            "end": [timestamp + pd.Timedelta(hours=-1)] * len(pocs_with_sessions),
            "id_pdc_itinerance": pocs_with_sessions,
        }
    )
    sampled_sessions = to_sampled_sessions(
        sessions, init_sessions, timestamp, samples_per_day
    )

    return to_sampled_state_poc(sampled_sessions, sampled_statuses)


@task(task_run_name="sampled_chunk-d-00-{day:%y-%m-%d}", cache_policy=NONE)
def get_sampled_state_poc_for_chunk(
    day: date,
    samples_per_day: int,
    statics_chunk: pd.DataFrame,
    sessions: pd.DataFrame,
    statuses: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate sampled_state_poc for a chunk."""
    statuses_chunk, sessions_chunk = filter_statuses_sessions(
        sessions, statuses, statics_chunk
    )
    sampled_state_poc_chunk = get_sampled_state_poc(
        day,
        samples_per_day,
        sessions_chunk,
        statuses_chunk,
    )
    return sampled_state_poc_chunk


@flow(
    flow_run_name="meta-d-{start:%y-%m-%d}",
)
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
    day = start.date()
    statuses = read_s3_data(day, environment, "qualicharge-statuses")
    sessions = read_s3_data(day, environment, "qualicharge-sessions")
    statics = read_statics(day, environment, min_power)
    chunks = [
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
    state_poc_d = to_state_poc_d(sampled_state_poc, samples_per_day)

    indicators_e2 = pd.DataFrame(
        {
            "target": "00",
            "value": len(state_poc_d),
            "code": "e2",
            "level": Level.NATIONAL,
            "period": PERIOD,
            "timestamp": day.isoformat(),
            "category": None,
            "extras": [
                {
                    "id_pdc_itinerance": list(state_poc_d[ID_POC]),
                    "occupe": list(state_poc_d["occupe"]),
                    "hors_service": list(state_poc_d["hors_service"]),
                    "libre": list(state_poc_d["libre"]),
                }
            ],
        }
    )
    desc_e2 = f"e2 report at {day} (period: {PERIOD})"
    flow_name_e2 = "e2-" + runtime.flow_run.name
    export_indicators(
        indicators_e2, environment, flow_name_e2, desc_e2, create_artifact, persist
    )

    sample_state_station = to_sampled_state_grp(
        sampled_state_poc, statics, ID_STATION, SATURATION_RATIO, OVERLOAD_RATIO
    )

    state_station_h = to_state_grp_h(
        sample_state_station, ID_STATION, SAMPLES, SATURE_H
    )
    state_station_d = to_state_grp_d(state_station_h, ID_STATION)

    indicators_e3 = pd.DataFrame(
        {
            "target": "00",
            "value": len(state_station_d),
            "code": "e3",
            "level": Level.NATIONAL,
            "period": PERIOD,
            "timestamp": day.isoformat(),
            "category": None,
            "extras": [
                {
                    "id_station_itinerance": list(state_station_d[ID_STATION]),
                    "nb_pdc": list(state_station_d["nb_pdc"]),
                    "nb_h": list(state_station_d["nb_h"]),
                    "hs": list(state_station_d["hs"]),
                    "inactif": list(state_station_d["inactif"]),
                    "sature_cum": list(state_station_d["sature_cum"]),
                    "sature_max": list(state_station_d["sature_max"]),
                    "surcharge": list(state_station_d["surcharge"]),
                    "actif": list(state_station_d["actif"]),
                }
            ],
        }
    )

    desc_e3 = f"e3 report at {day} (period: {PERIOD})"
    flow_name_e3 = "e3-" + runtime.flow_run.name
    export_indicators(
        indicators_e3, environment, flow_name_e3, desc_e3, create_artifact, persist
    )
    return (indicators_e2, indicators_e3)
