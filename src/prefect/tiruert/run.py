"""Tiruert calculation flows."""

import logging
from datetime import date
from string import Template

import pandas as pd
from prefect import flow, task
from sqlalchemy.orm import Session

from indicators.db import get_api_db_engine
from indicators.types import Environment
from indicators.utils import export_indicators

logger = logging.getLogger(__name__)

OPERATIONAL_UNIT_WITH_SESSIONS_TEMPLATE = Template(
    """
    SELECT
      SUBSTRING(_pointdecharge.id_pdc_itinerance for 5) AS code,
      Count(Session.id) AS COUNT
    FROM
      Session
      JOIN _pointdecharge ON _pointdecharge.id = Session.point_de_charge_id
    WHERE
      Session.start >= '$from_date'
      AND Session.start < '$to_date'
    GROUP BY
      code
    ORDER BY
      code
    """
)

OPERATIONAL_UNIT_SESSIONS_FOR_A_DAY_TEMPLATE = Template(
    """
    SELECT
      Amenageur.nom_amenageur AS entity,
      Amenageur.siren_amenageur AS siren,
      SUBSTRING(_pointdecharge.id_pdc_itinerance FOR 5) AS code,
      Station.id_station_itinerance AS id_station_itinerance,
      _pointdecharge.id_pdc_itinerance AS id_pdc_itinerance,
      _pointdecharge.puissance_nominale AS max_power,
      Session.id AS session_id,
      Session.start AS "from",
      Session.end AS "to",
      Session.energy AS energy,
      Session.point_de_charge_id
    FROM
      Session
      LEFT JOIN _pointdecharge ON Session.point_de_charge_id = _pointdecharge.id
      LEFT JOIN Station ON _pointdecharge.station_id = Station.id
      LEFT JOIN Amenageur ON Station.amenageur_id = amenageur.id
    WHERE
      Session.start >= '$from_date'
      AND Session.start < '$to_date'
      AND SUBSTRING(_pointdecharge.id_pdc_itinerance FOR 5) = '$operational_unit_code'
    ORDER BY
      id_pdc_itinerance,
      "from"
    """
)

SESSION_ENE_MAX = 1000.0  # in kWh


@task
def get_operational_units_for_period(
    environment: Environment, from_date: date, to_date: date
) -> pd.DataFrame:
    """Get operational units for a defined period.

    Args:
    environment (Environment): target environment
    from_date (date): included
    to_date (date): excluded
    """
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            OPERATIONAL_UNIT_WITH_SESSIONS_TEMPLATE.substitute(
                {"from_date": from_date, "to_date": to_date}
            ),
            con=session.connection(),
        )


@task
def get_sessions(
    environment: Environment, from_date: date, to_date: date, code: str
) -> pd.DataFrame:
    """Get sessions for a period and an operational unit.

    Args:
    environment (Environment): target environment
    from_date (date): included
    to_date (date): excluded
    code (str): operational unit code (e.g. FRXXX)

    """
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            OPERATIONAL_UNIT_SESSIONS_FOR_A_DAY_TEMPLATE.substitute(
                {
                    "operational_unit_code": code,
                    "from_date": from_date,
                    "to_date": to_date,
                }
            ),
            con=session.connection(),
        )


def negs(row):
    """NEGS data quality test."""
    return (row["to"] - row["from"]).total_seconds() < 0


def eneu(row):
    """ENEU data quality test."""
    return row["energy"] > SESSION_ENE_MAX


def enea_max(row):
    """ENEA data quality test maximal value."""
    return ((row["to"] - row["from"]).total_seconds() / 3600) * row["max_power"]


def enea(row):
    """ENEA data quality test."""
    return row["energy"] > enea_max(row) * 1.1


def odus(row):
    """0DUS data quality test."""
    return negs(row) and row["energy"] > 1


def enex(row):
    """ENEX data quality test."""
    return row["energy"] > SESSION_ENE_MAX and row["energy"] > enea_max(row) * 2.0


def flag_duplicates(sessions: pd.DataFrame) -> pd.DataFrame:
    """Flag duplicated or overlaping sessions."""
    # Ease comparison with previous row (and avoid iterating over dataframe rows)
    sessions["p_id_pdc_itinerance"] = pd.concat(
        [pd.Series([None]), sessions["id_pdc_itinerance"][:-1]]
    ).reset_index(drop=True)
    sessions["p_from"] = pd.concat(
        [pd.Series([None]), sessions["from"][:-1]]
    ).reset_index(drop=True)
    sessions["p_to"] = pd.concat([pd.Series([None]), sessions["to"][:-1]]).reset_index(
        drop=True
    )

    # Real duplicates
    sessions["duplicate"] = (
        (sessions["from"] == sessions["p_from"])
        & (sessions["to"] == sessions["p_to"])
        & (sessions["id_pdc_itinerance"] == sessions["p_id_pdc_itinerance"])
    )

    # Overlaps
    sessions["overlap"] = (sessions["from"] < sessions["p_to"]) & (
        sessions["id_pdc_itinerance"] == sessions["p_id_pdc_itinerance"]
    )

    return sessions


def flag_bad_sessions(sessions: pd.DataFrame) -> pd.DataFrame:
    """Flag bad sessions."""
    sessions["enea_max"] = sessions.apply(enea_max, axis=1)
    sessions["negs"] = sessions.apply(negs, axis=1)
    sessions["eneu"] = sessions.apply(eneu, axis=1)
    sessions["enea"] = sessions.apply(enea, axis=1)
    sessions["odus"] = sessions.apply(odus, axis=1)
    sessions["enex"] = sessions.apply(enex, axis=1)
    return sessions


@task
def filter_sessions(sessions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean sent sessions.

    Tasks:
    - Remove duplicates
    - Remove aberrant sessions

    Returns a tuple with (filtered_sessions, ignored_sessions)
    """
    sessions = flag_duplicates(sessions)
    sessions = flag_bad_sessions(sessions)

    to_ignore = sessions[
        sessions.negs
        | sessions.eneu
        | sessions.enea
        | sessions.odus
        | sessions.enex
        | sessions.overlap
        | sessions.duplicate
    ]

    return sessions.iloc[sessions.index.difference(to_ignore.index)], to_ignore


@task
def save_tiruert(
    sessions: pd.DataFrame, environment: Environment, from_date: date, to_date: date
) -> None:
    """Save the daily TIRUERT to the indicators database."""


@flow
def tiruert_for_period_and_operational_unit(
    environment: Environment, from_date: date, to_date: date, code: str
):
    """Calculate the TIRUERT for a defined period and an operational unit."""
    sessions = get_sessions(environment, from_date, to_date, code)
    sessions, ignored = filter_sessions(sessions)

    # FIXME
    # This is temporary
    export_indicators(
        indicators=sessions,
        environment=environment,
        flow_name="session-for-tiruert",
        description=(
            "Sessions that will be considered as valid for TIRUERT calculation."
        ),
        create_artifact=True,
        persist=False,
    )
    export_indicators(
        indicators=ignored,
        environment=environment,
        flow_name="ignored-session-for-tiruert",
        description=("Sessions that will be ignored for TIRUERT calculation."),
        create_artifact=True,
        persist=False,
    )

    # TODO
    save_tiruert(sessions, environment, from_date, to_date)


@flow
def tiruert_for_period(environment: Environment, from_date: date, to_date: date):
    """Calculate the TIRUERT for a defined period."""
    operational_units = get_operational_units_for_period(
        environment, from_date, to_date
    )
    for code in operational_units["code"]:
        tiruert_for_period_and_operational_unit(environment, from_date, to_date, code)
