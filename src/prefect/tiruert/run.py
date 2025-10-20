"""Tiruert calculation flows."""

import logging
import os
from datetime import date, datetime, timedelta
from string import Template

import pandas as pd
from prefect import flow, task
from prefect.states import Failed
from pyarrow import fs
from sqlalchemy.orm import Session

from indicators.db import get_api_db_engine
from indicators.models import IndicatorPeriod, Level
from indicators.types import Environment
from indicators.utils import export_indicators

logger = logging.getLogger(__name__)

OPERATIONAL_UNIT_WITH_SESSIONS_TEMPLATE = Template(
    """
    SELECT DISTINCT
      operationalunit.code AS code,
      Count(Session.id) AS COUNT
    FROM
      Session
      INNER JOIN _pointdecharge ON _pointdecharge.id = Session.point_de_charge_id
      INNER JOIN _station ON _station.id = _pointdecharge.station_id
      INNER JOIN operationalunit ON operationalunit.id = _station.operational_unit_id
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
      operationalunit.code AS code,
      _station.id_station_itinerance AS id_station_itinerance,
      _pointdecharge.id_pdc_itinerance AS id_pdc_itinerance,
      _pointdecharge.puissance_nominale AS max_power,
      Session.id AS session_id,
      Session.start AS "from",
      Session.end AS "to",
      Session.energy AS energy,
      Session.point_de_charge_id
    FROM
      Session
      LEFT JOIN _pointdecharge ON _pointdecharge.id = Session.point_de_charge_id
      LEFT JOIN _station ON _station.id = _pointdecharge.station_id
      LEFT JOIN operationalunit ON operationalunit.id = _station.operational_unit_id
      LEFT JOIN Amenageur ON _station.amenageur_id = amenageur.id
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
def archive_ignored_session_for_day(
    ignored: pd.DataFrame,
    day: date,
    code: str,
):
    """Archive ignored sessions to S3."""
    bucket = "qualicharge-sessions"
    s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", None)
    if s3_endpoint_url is None:
        return Failed(message="S3_ENDPOINT_URL environment variable not set.")

    # Target bucket
    s3 = fs.S3FileSystem(endpoint_override=s3_endpoint_url)
    dir_path = f"{bucket}/{day.year}/{day.month}/{day.day}"
    file_path = f"{dir_path}/ignored-{code}.parquet"

    # Default output stream method
    s3_open_output_stream = s3.open_output_stream

    # Convert UUID to str for pyarrow
    ignored["session_id"] = ignored["session_id"].apply(str)
    ignored["point_de_charge_id"] = ignored["point_de_charge_id"].apply(str)

    # Start writing dataset to the target bucket
    s3.create_dir(dir_path)
    with s3_open_output_stream(file_path) as archive:
        ignored.to_parquet(archive)


@task
def save_indicator_for_day(
    sessions: pd.DataFrame, environment: Environment, day: date, code: str
):
    """Save cumulated sessions as an indicator."""
    # Sum by EVSE pool for an operational unit for the day
    by_station_report = sessions.groupby(
        ["entity", "siren", "code", "id_station_itinerance"]
    )["energy"].sum()
    by_station_report /= 1000.0  # Convert to MWh
    by_station_report_df = by_station_report.reset_index()

    # Build result DataFrame
    indicators = pd.DataFrame(
        {
            "target": code,
            # total for period in MWh
            "value": by_station_report_df["energy"].sum(),
            "code": "tirue",
            "level": Level.OU,
            "period": IndicatorPeriod.DAY,
            "timestamp": datetime(day.year, day.month, day.day).isoformat(),
            "category": None,
            "extras": [by_station_report_df.to_dict(orient="records")],
        }
    )

    export_indicators(
        indicators=indicators,
        environment=environment,
        flow_name="tiruert-for-period-and-operational-unit",
        description="Sessions that will be used for TIRUERT calculation.",
        create_artifact=False,
        persist=True,
    )


@flow
def tiruert_for_day_and_operational_unit(
    environment: Environment, day: date, code: str
):
    """Calculate the TIRUERT for a defined day and an operational unit."""
    sessions = get_sessions(environment, day, day + timedelta(days=1), code)
    sessions, ignored = filter_sessions(sessions)
    save_indicator_for_day(sessions, environment, day, code)
    archive_ignored_session_for_day(ignored, day, code)


@flow
def tiruert_for_day(environment: Environment, day: date):
    """Calculate the TIRUERT for a defined day."""
    operational_units = get_operational_units_for_period(
        environment, day, day + timedelta(days=1)
    )
    for code in operational_units["code"]:
        tiruert_for_day_and_operational_unit(environment, day, code)
