"""QualiCharge prefect indicators: extract.utils.

Common indicators functions and constants.
"""

from datetime import date, timedelta
from string import Template

import numpy as np
import pandas as pd
from pandas import NamedAgg
from prefect import task
from sqlalchemy.orm import Session

from indicators.db import get_indicators_db_engine
from indicators.models import IndicatorPeriod
from indicators.types import Environment

PDC_STATION_FOR_DAY_TEMPLATE = """
SELECT
  value,
  extras
FROM
  $environment
WHERE
  code = 'e5' and level = 0  and period = 'd' and target = '00'
  AND timestamp >= '$from_date'
  AND timestamp < '$to_date'
ORDER BY
  value desc
"""
PERIOD = IndicatorPeriod.DAY
ID_POC: str = "id_pdc_itinerance"
ID_STATION: str = "id_station_itinerance"
MAX_SESSION_DURATION_HOURS: float = 10
START_FULL_USE: float = 0.99
END_FULL_USE: float = 0.8


def hysteresis(
    x: pd.Series, low_hysteresis_level: float, high_hysteresis_level: float
) -> pd.Series:
    """Apply hysteresis to a Series with given low and high hysteresis levels."""
    high = x >= high_hysteresis_level
    low_or_high = (x < low_hysteresis_level) | high
    ind_low_or_high = np.nonzero(low_or_high)[0]
    if not ind_low_or_high.size:  # prevent index error if ind_low_or_high is empty
        return pd.Series(False, index=x.index)
    cnt = np.cumsum(low_or_high)
    return pd.Series(
        np.where(cnt, high[ind_low_or_high[cnt - 1]], False), index=x.index
    )


def maxi_duration(
    state_grp: pd.DataFrame, group_name: str, sorted: str, values: str
) -> pd.DataFrame:
    """Calculate the maximum number of periods of a given value for each group."""
    df = state_grp.sort_values(by=[group_name, sorted]).reset_index(drop=True)

    groups = (
        df[values]
        .ne(df.groupby(group_name)[values].shift())
        .groupby(df[group_name])
        .cumsum()
    )

    valid_groups = df[df[values]].assign(valid_group=groups[df[values]])

    maxi_period = valid_groups.groupby([group_name, "valid_group"]).agg(
        first=(sorted, "first"), last=(sorted, "last"), duration=(sorted, "count")
    )
    maxi_period = maxi_period.loc[maxi_period.groupby(level=0)["duration"].idxmax()]
    return maxi_period.reset_index()


def hourly_maximum(
    state_grp: pd.DataFrame,
    group_name: str,
    sorted: str,
    values: str,
    samples_per_hour: int,
) -> pd.DataFrame:
    """Calculate the hourly maximum of a given value for each group."""
    df = state_grp.sort_values(by=[group_name, sorted]).reset_index(drop=True)
    cumul_hours = (
        df.groupby(group_name)[values]
        .rolling(window=samples_per_hour, min_periods=1)
        .sum()
    )
    cumul_hours_max = cumul_hours.groupby(group_name).idxmax()
    hourly_max = (
        cumul_hours.loc[cumul_hours_max]
        .reset_index()
        .rename(columns={"level_1": "index_state_grp", values: values + "_max"})
    )
    return hourly_max


def filter_sessions_duration(
    sessions: pd.DataFrame,
    min_duration: timedelta = timedelta(),
    max_duration: timedelta = timedelta(hours=24),
) -> pd.DataFrame:
    """Filter sessions based on minimum and maximum duration."""
    unic = ["start", "end", "id_pdc_itinerance"]
    sessions["duration"] = sessions["end"] - sessions["start"]
    filtered_sessions = (
        sessions[
            (sessions["duration"] > min_duration)
            & (sessions["duration"] < max_duration)
        ]
        .copy()
        .drop_duplicates(subset=unic)
        .reset_index(drop=True)
    )
    return filtered_sessions


def get_pdc_station_for_day(from_date: date, environment: Environment) -> pd.DataFrame:
    """Get points of charge and stations for a given day."""
    query_template = Template(PDC_STATION_FOR_DAY_TEMPLATE)
    query_params = {
        "from_date": from_date,
        "to_date": from_date + timedelta(days=1),
        "environment": environment.value,
    }
    with Session(get_indicators_db_engine()) as session:
        e5_data = pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )
    if e5_data.empty:
        return pd.DataFrame()
    pdc_station = pd.DataFrame(e5_data["extras"][0])
    if len(pdc_station) != e5_data["value"][0]:
        return pd.DataFrame()
    return pdc_station


def to_sampled_statuses(
    data: pd.DataFrame,
    init_data: pd.DataFrame,
    timestamp: pd.Timestamp,
    samples_per_day: int,
    min_duration: timedelta = timedelta(),
) -> pd.DataFrame:
    """Generate sampled statuses for a given date.

    Generation is based on a set of statuses and initial values.
    The output states ('etat_pdc') are either 'en_service' or 'hors_service'
    ('inconnu' value is not taken into account).
    The output states ('occupation_pdc') are either 'occupe', 'libre' or 'inconnu'.
    """
    samples = pd.date_range(
        start=timestamp,
        end=timestamp + pd.Timedelta(days=1),
        periods=samples_per_day + 1,
    )
    periode = pd.DataFrame({"periode": samples[0:samples_per_day]})
    state = pd.concat([data, init_data]).sort_values(
        by=["id_pdc_itinerance", "horodatage"]
    )
    state = state[state["etat_pdc"] != "inconnu"].copy().reset_index(drop=True)
    state["f_horodatage"] = state["horodatage"].shift(-1)
    state.loc[state.index[-1], "f_horodatage"] = samples[samples_per_day]
    state["f_id_pdc_itinerance"] = state["id_pdc_itinerance"].shift(-1)
    state.loc[state.index[-1], "f_id_pdc_itinerance"] = "aucun"

    # remove statuses with short duration
    state["duration"] = state["f_horodatage"] - state["horodatage"]
    filtered_state = (
        state[
            (state["duration"] > min_duration)
            | (state["id_pdc_itinerance"] != state["f_id_pdc_itinerance"])
        ]
        .copy()
        .reset_index(drop=True)
    )
    filtered_state["f_horodatage"] = list(filtered_state["horodatage"])[
        1 : len(filtered_state)
    ] + [samples[samples_per_day]]
    filtered_state["f_id_pdc_itinerance"] = list(filtered_state["id_pdc_itinerance"])[
        1 : len(filtered_state)
    ] + ["aucun"]

    # create sampled statuses
    crossed = pd.merge(filtered_state, periode, how="cross")
    sampled = crossed[
        (crossed["id_pdc_itinerance"].eq(crossed["f_id_pdc_itinerance"]))
        & (crossed["periode"] >= crossed["horodatage"])
        & (crossed["periode"] < crossed["f_horodatage"])
    ]
    sampled = sampled[["periode", "etat_pdc", "occupation_pdc", "id_pdc_itinerance"]]

    return sampled.sort_values(by=["id_pdc_itinerance", "periode"]).reset_index(
        drop=True
    )


def to_sampled_sessions(
    data: pd.DataFrame,
    init_data: pd.DataFrame,
    timestamp: pd.Timestamp,
    samples_per_day: int,
) -> pd.DataFrame:
    """Generate sampled sessions for a given date.

    Generation is based on a set of sessions and initial values.
    Input data: set of sessions and initial values.
    The output states ('occupation_pdc') are either 'occupe' or 'libre'.
    The 'inconnu' value is not taken into account.
    """
    # init variables
    samples = pd.date_range(
        start=timestamp,
        end=timestamp + pd.Timedelta(days=1),
        periods=samples_per_day + 1,
    )
    periode = pd.DataFrame({"periode": samples[0:samples_per_day]})
    sessions = (
        pd.concat([data, init_data])
        .sort_values(by=["id_pdc_itinerance", "start"])
        .reset_index(drop=True)
    )

    # create sampled sessions
    sessions["occupation_pdc"] = "occupe"
    crossed = pd.merge(sessions, periode, how="cross")
    sampled = crossed[
        (
            (crossed["periode"] >= crossed["start"])
            & (crossed["periode"] < crossed["end"])
        )
    ]
    sampled = sampled[["periode", "occupation_pdc", "id_pdc_itinerance"]]
    non_occupe = pd.merge(
        periode,
        pd.DataFrame({"id_pdc_itinerance": sessions["id_pdc_itinerance"].unique()}),
        how="cross",
    )
    sampled = pd.merge(
        non_occupe, sampled, how="left", on=["id_pdc_itinerance", "periode"]
    ).fillna("f_libre")

    return sampled.sort_values(by=["id_pdc_itinerance", "periode"]).reset_index(
        drop=True
    )


def to_sampled_state_poc(
    sessions: pd.DataFrame, statuses: pd.DataFrame
) -> pd.DataFrame:
    """Combine the states derived from sessions with those derived from statuses.

    The session 'occupe' state takes precedence over the status state.
    A session's 'f_libre' (not occupied) state translates to the 'hors_service' state if
    The status state is 'hors_service'; otherwise, it translates to the 'libre' state.
    The 'pseudo-libre' corresponds to a 'libre' status with a session that is not.
    The 'pseudo-occupe' corresponds to a 'occupe' status with a session that is not.
    """
    statuses = statuses.rename(columns={"occupation_pdc": "occupation_pdc_status"})
    merged = pd.merge(
        sessions, statuses, how="outer", on=["id_pdc_itinerance", "periode"]
    ).fillna("aaa")

    # ! The state names are chosen so that alphabetical sorting respects
    # the order of priority.
    merged["state"] = (
        merged[["etat_pdc", "occupation_pdc"]]
        .agg("max", axis=1)
        .replace("en_service", "libre")
    )
    merged["pseudo_libre"] = (
        merged["occupation_pdc_status"].eq("libre")
        & merged["occupation_pdc"].ne("f_libre")
        & merged["etat_pdc"].eq("en_service")
    )
    merged["pseudo_occupe"] = (
        merged["occupation_pdc_status"].eq("occupe")
        & merged["occupation_pdc"].ne("occupe")
        & merged["etat_pdc"].eq("en_service")
    )
    merged = merged[
        ["id_pdc_itinerance", "periode", "state", "pseudo_libre", "pseudo_occupe"]
    ].replace("f_libre", "libre")

    return merged.sort_values(by=["id_pdc_itinerance", "periode"]).reset_index(
        drop=True
    )


@task(task_run_name="state-poc-d")
def to_state_poc(state_poc: pd.DataFrame, samples_per_day: int) -> pd.DataFrame:
    """Generate daily states for the charge points based on their sampled state.

    The time spent in each state is returned in minutes.
    """
    samples_per_hour = samples_per_day // 24
    sample_duration = 24 * 60 / samples_per_day

    sampled = state_poc[
        ["id_pdc_itinerance", "state", "pseudo_libre", "pseudo_occupe", "periode"]
    ].reset_index()
    sampled["occupe"] = sampled["state"] == "occupe"
    sampled["hors_service"] = sampled["state"] == "hors_service"
    sampled["libre"] = sampled["state"] == "libre"
    occupe_max = hourly_maximum(
        sampled, "id_pdc_itinerance", "periode", "occupe", samples_per_hour
    )
    occupe_max["occupe_max"] = occupe_max["occupe_max"] * sample_duration

    state_d = (
        sampled[
            [
                "id_pdc_itinerance",
                "occupe",
                "hors_service",
                "libre",
                "pseudo_libre",
                "pseudo_occupe",
            ]
        ]
        .groupby(["id_pdc_itinerance"])
        .agg("sum")
        .reset_index()
    )

    for etat in ["occupe", "hors_service", "libre", "pseudo_libre", "pseudo_occupe"]:
        state_d[etat] = state_d[etat] * sample_duration
    full_state_d = pd.merge(
        state_d,
        occupe_max[["id_pdc_itinerance", "occupe_max"]],
        on="id_pdc_itinerance",
        how="left",
    ).fillna(0)
    return full_state_d[
        [
            "id_pdc_itinerance",
            "occupe",
            "occupe_max",
            "hors_service",
            "libre",
            "pseudo_libre",
            "pseudo_occupe",
        ]
    ]


@task(task_run_name="sampled_grp")
def to_sampled_state_grp(  # noqa: PLR0913
    state_poc: pd.DataFrame,
    pdc_group: pd.DataFrame,
    group_name: str,
    saturation_ratio: float,
    overload_ratio: float,
    add_full_use: bool = False,
    add_latency: bool = False,
) -> pd.DataFrame:
    """Generate the aggregated states of a set of charge points.

    "surcharge" occurs when the number of charge points falls below 'overload_ratio'
    value, and "sature" occurs below 'saturation_ratio' value.
    Each state is represented by a boolean value as well as an aggregated numeric value
    ('hs': 1, 'inactif': 2, 'actif': 3, 'surcharge': 4, 'sature': 5).
    """
    returned_fields = [
        group_name,
        "periode",
        "occupe",
        "hors_service",
        "libre",
        "pleine_utilisation",
        "pseudo_libre",
        "pseudo_occupe",
        "nb_pdc",
        "hs",
        "inactif",
        "pu",
        "sature",
        "surcharge",
        "actif",
        "state",
    ]
    nb_pdc = (
        pdc_group.groupby([group_name])
        .count()
        .rename(columns={"id_pdc_itinerance": "nb_pdc"})
    )
    merged = pd.merge(state_poc, pdc_group, how="left", on="id_pdc_itinerance")
    merged["occupe"] = merged["state"] == "occupe"
    merged["hors_service"] = merged["state"] == "hors_service"
    merged["libre"] = merged["state"] == "libre"
    # add a 5 min interval for 'pleine utilisation'
    if add_latency:
        occupe_hs = merged["occupe"] | merged["hors_service"]
        merged["pleine_utilisation"] = (
            occupe_hs | occupe_hs.shift(fill_value=False)
        ) & (
            merged["id_pdc_itinerance"]
            == merged["id_pdc_itinerance"].shift(fill_value="")
        )
    else:
        merged["pleine_utilisation"] = merged["occupe"]
    grouped = (
        merged[
            [
                group_name,
                "periode",
                "occupe",
                "hors_service",
                "libre",
                "pleine_utilisation",
                "pseudo_libre",
                "pseudo_occupe",
            ]
        ]
        .groupby([group_name, "periode"])
        .sum()
        .reset_index()
    )
    grouped = pd.merge(grouped, nb_pdc, how="left", on=group_name)

    # a poc without statuses and without sessions is considered as hors_service
    grouped["hors_service"] = grouped["nb_pdc"] - grouped["libre"] - grouped["occupe"]

    grouped["hs"] = ((grouped["libre"] + grouped["occupe"]) == 0) & (
        grouped["hors_service"] > 0
    )
    grouped["inactif"] = ~grouped["hs"] & (grouped["occupe"] == 0)
    grouped["sature"] = (
        ~grouped["hs"]
        & ~grouped["inactif"]
        & (grouped["libre"] / grouped["nb_pdc"] < saturation_ratio)
    )
    grouped["surcharge"] = (
        ~grouped["hs"]
        & ~grouped["inactif"]
        & ~grouped["sature"]
        & (grouped["libre"] / grouped["nb_pdc"] < overload_ratio)
    )
    grouped["actif"] = (
        ~grouped["hs"]
        & ~grouped["inactif"]
        & ~grouped["sature"]
        & ~grouped["surcharge"]
    )
    grouped["state"] = (
        grouped["hs"]
        + grouped["inactif"] * 2
        + grouped["actif"] * 3
        + grouped["surcharge"] * 4
        + grouped["sature"] * 5
    )

    if add_full_use:
        not_full_use = 0
        maybe_full_use = 0.5
        full_use = 1

        full_use_rate = (
            grouped["pleine_utilisation"] + grouped["hors_service"]
        ) / grouped["nb_pdc"]
        tmp_full_use = pd.Series(
            pd.cut(
                full_use_rate,
                [-np.inf, END_FULL_USE, START_FULL_USE, np.inf],
                labels=[not_full_use, maybe_full_use, full_use],
            ),
            index=full_use_rate.index,
        )
        grouped["pu"] = tmp_full_use.where(
            tmp_full_use != maybe_full_use,
            np.where(
                hysteresis(tmp_full_use, maybe_full_use, full_use),
                full_use,
                not_full_use,
            ),
        ).astype("bool")
    else:
        grouped["pu"] = False

    return grouped[returned_fields]


@task(task_run_name="state-grp")
def to_state_grp(
    state_grp: pd.DataFrame,
    group_name: str,
    samples_per_day: int,
) -> pd.DataFrame:
    """Generate daily states based on the sampled state of a set of charge points.

    The time spent in each state is returned in minutes.
    """
    sample_duration = 24 * 60 / samples_per_day
    samples_per_hour = samples_per_day // 24

    sampled = state_grp.reset_index()

    hourly_max = hourly_maximum(
        sampled, group_name, "periode", "sature", samples_per_hour
    )
    pu_max = hourly_maximum(sampled, group_name, "periode", "pu", samples_per_hour)
    pu_duration = maxi_duration(sampled, group_name, "periode", "pu")

    hourly_max["sature_max"] = hourly_max["sature_max"] * sample_duration
    hourly_max["pu_max"] = pu_max["pu_max"] * sample_duration
    pu_duration["pu_len"] = pu_duration["duration"] * sample_duration

    grouped = sampled.groupby([group_name, "nb_pdc"])
    state_grp = (
        grouped.agg(
            hs=NamedAgg("hs", "sum"),
            inactif=NamedAgg("inactif", "sum"),
            pu_cum=NamedAgg("pu", "sum"),
            sature_cum=NamedAgg("sature", "sum"),
            surcharge=NamedAgg("surcharge", "sum"),
            actif=NamedAgg("actif", "sum"),
        )
        * sample_duration
    ).reset_index()
    full_state_grp = pd.merge(
        state_grp,
        hourly_max[[group_name, "sature_max", "pu_max"]],
        on=group_name,
        how="left",
    ).fillna(0)
    full_state_grp = pd.merge(
        full_state_grp, pu_duration[[group_name, "pu_len"]], on=group_name, how="left"
    ).fillna(0)

    return full_state_grp
