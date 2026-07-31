"""QualiCharge prefect indicators: extract.utils.

Common indicators functions and constants.
"""

from datetime import date, timedelta
from string import Template

import pandas as pd
from pandas import NamedAgg
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
    The output states ('etat_pdc') are either 'en_service' or 'hors_service'.
    The 'inconnu' value is not taken into account.
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
    state = state[(state["etat_pdc"] != "inconnu")]
    state["f_horodatage"] = list(state["horodatage"])[1 : len(state)] + [
        samples[samples_per_day]
    ]
    state["f_id_pdc_itinerance"] = list(state["id_pdc_itinerance"])[1 : len(state)] + [
        "aucun"
    ]
    # remove statuses with short duration
    state["duration"] = state["f_horodatage"] - state["horodatage"]
    filtered_state = state[
        (state["duration"] > min_duration)
        | (state["id_pdc_itinerance"] != state["f_id_pdc_itinerance"])
    ].copy()
    filtered_state["f_horodatage"] = list(filtered_state["horodatage"])[
        1 : len(filtered_state)
    ] + [samples[samples_per_day]]
    filtered_state["f_id_pdc_itinerance"] = list(filtered_state["id_pdc_itinerance"])[
        1 : len(filtered_state)
    ] + ["aucun"]

    # create sampled statuses
    crossed = pd.merge(filtered_state, periode, how="cross")
    sampled = crossed[
        (
            (crossed["id_pdc_itinerance"].eq(crossed["f_id_pdc_itinerance"]))
            & (crossed["periode"] >= crossed["horodatage"])
            & (crossed["periode"] < crossed["f_horodatage"])
        )
        | (
            ~(crossed["id_pdc_itinerance"].eq(crossed["f_id_pdc_itinerance"]))
            & (crossed["periode"] >= crossed["horodatage"])
        )
    ]
    sampled = sampled[["periode", "etat_pdc", "id_pdc_itinerance"]]

    return sampled.sort_values(by=["id_pdc_itinerance", "periode"]).reset_index(
        drop=True
    )


def to_sampled_sessions(  # noqa: PLR0913
    data: pd.DataFrame,
    init_data: pd.DataFrame,
    timestamp: pd.Timestamp,
    samples_per_day: int,
    min_duration: timedelta = timedelta(),
    max_duration: timedelta = timedelta(hours=24),
) -> pd.DataFrame:
    """Generate sampled sessions for a given date.

    Generation is based on a set of sessions and initial values.
    Input data: set of sessions and initial values.
    The output states ('occupation_pdc') are either 'occupe' or 'libre'.
    The 'inconnu' value is not taken into account.
    """
    samples = pd.date_range(
        start=timestamp,
        end=timestamp + pd.Timedelta(days=1),
        periods=samples_per_day + 1,
    )
    periode = pd.DataFrame({"periode": samples[0:samples_per_day]})
    sessions = pd.concat([data, init_data]).sort_values(
        by=["id_pdc_itinerance", "start"]
    )
    # remove invalid sessions : duplicates, short duration, long duration
    unic = ["start", "end", "id_pdc_itinerance"]
    sessions["duration"] = sessions["end"] - sessions["start"]
    filtered_sessions = (
        sessions[
            (sessions["duration"] > min_duration)
            & (sessions["duration"] < max_duration)
        ]
        .copy()
        .drop_duplicates(subset=unic)
    )

    # create sampled sessions
    filtered_sessions["occupation_pdc"] = "occupe"
    crossed = pd.merge(filtered_sessions, periode, how="cross")
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
    the status state is 'hors_service'; otherwise, it translates to the 'libre' state.
    """
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
    merged = merged[["id_pdc_itinerance", "periode", "state"]].replace(
        "f_libre", "libre"
    )

    return merged.sort_values(by=["id_pdc_itinerance", "periode"]).reset_index(
        drop=True
    )


def to_state_poc_d(state_poc: pd.DataFrame, samples_per_day: int) -> pd.DataFrame:
    """Generate daily states for the charge points based on their sampled state.

    The time spent in each state is returne d in minutes.
    """
    sampled = state_poc[["id_pdc_itinerance", "state"]].reset_index()
    sampled["occupe"] = sampled["state"] == "occupe"
    sampled["hors_service"] = sampled["state"] == "hors_service"
    sampled["libre"] = sampled["state"] == "libre"

    state_d = sampled.groupby(["id_pdc_itinerance"]).agg("sum").reset_index()

    for etat in ["occupe", "hors_service", "libre"]:
        state_d[etat] = state_d[etat] * 60 * 24 / samples_per_day

    return state_d[["id_pdc_itinerance", "occupe", "hors_service", "libre"]]


def to_sampled_state_grp(
    state_poc: pd.DataFrame,
    pdc_group: pd.DataFrame,
    group_name: str,
    saturation_ratio: float,
    overload_ratio: float,
) -> pd.DataFrame:
    """Generate the aggregated states of a set of charge points.

    "surcharge" occurs when the number of charge points falls below 'overload_ratio'
    value, and "sature" occurs below 'saturation_ratio' value.
    Each state is represented by a boolean value as well as an aggregated numeric value
    ('hs': 1, 'inactif': 2, 'actif': 3, 'surcharge': 4, 'sature': 5).
    """
    nb_pdc = (
        pdc_group.groupby([group_name])
        .count()
        .rename(columns={"id_pdc_itinerance": "nb_pdc"})
    )
    merged = pd.merge(state_poc, pdc_group, how="left", on="id_pdc_itinerance")
    merged["occupe"] = merged["state"] == "occupe"
    merged["hors_service"] = merged["state"] == "hors_service"
    merged["libre"] = merged["state"] == "libre"

    grouped = (
        merged[[group_name, "periode", "occupe", "hors_service", "libre"]]
        .groupby([group_name, "periode"])
        .sum()
        .reset_index()
    )
    grouped = pd.merge(grouped, nb_pdc, how="left", on=group_name)

    grouped["hs"] = (grouped["libre"] + grouped["occupe"] == 0) & (
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

    return grouped[
        [
            group_name,
            "periode",
            "occupe",
            "hors_service",
            "libre",
            "nb_pdc",
            "hs",
            "inactif",
            "sature",
            "surcharge",
            "actif",
            "state",
        ]
    ]


def to_state_grp_h(
    state_grp: pd.DataFrame,
    group_name: str,
    samples_per_day: int,
    duree_etat_min: float,
) -> pd.DataFrame:
    """Generate hourly states based on the sampled state of a set of charge points.

    The time spent in each state is returned in minutes.
    Two boolean hourly states, 'sature_h' and 'surcharge_h', are calculated based on a
    threshold for the time spent in the state.
    """
    nb_ech_hour = samples_per_day / 24

    sampled = state_grp.reset_index()
    sampled["periode_h"] = sampled["periode"].dt.hour
    sampled["periode"] = sampled["periode"].dt.date

    sampled_h = sampled.groupby([group_name, "nb_pdc", "periode", "periode_h"]).agg(
        "sum"
    )
    sampled_h = sampled_h / nb_ech_hour
    for etat in ["hs", "inactif", "sature", "surcharge", "actif"]:
        sampled_h[etat] = sampled_h[etat] * 60

    sampled_h["sature_h"] = (sampled_h["sature"] + sampled_h["hs"]) >= duree_etat_min
    sampled_h["surcharge_h"] = ~sampled_h["sature_h"] & (
        (sampled_h["surcharge"] + sampled_h["sature"] + sampled_h["hs"])
        >= duree_etat_min
    )

    sampled_h = sampled_h.reset_index()

    return sampled_h[
        [
            group_name,
            "periode",
            "periode_h",
            "nb_pdc",
            "hs",
            "inactif",
            "sature",
            "surcharge",
            "actif",
            "sature_h",
            "surcharge_h",
        ]
    ]


def to_state_grp_d(
    state_grp_h: pd.DataFrame,
    group_name: str,
) -> pd.DataFrame:
    """Generate daily states from the hourly state of a set of charge points.

    The time spent in each state is returned in minutes.
    """
    grouped = state_grp_h.groupby([group_name, "periode"])
    state_grp_d = grouped.agg(
        nb_pdc=NamedAgg("nb_pdc", "max"),
        nb_h=NamedAgg("periode", "count"),
        hs=NamedAgg("hs", "sum"),
        inactif=NamedAgg("inactif", "sum"),
        sature_cum=NamedAgg("sature", "sum"),
        sature_max=NamedAgg("sature", "max"),
        surcharge=NamedAgg("surcharge", "sum"),
        actif=NamedAgg("actif", "sum"),
    ).reset_index()

    return state_grp_d
