"""Tiruert calculation flows."""

from datetime import date
from string import Template

import pandas as pd
from prefect import flow, task
from sqlalchemy.orm import Session

from indicators.db import get_api_db_engine
from indicators.types import Environment

OPERATIONAL_UNIT_WITH_SESSIONS_TEMPLATE = Template(
    """
    SELECT
      OperationalUnit.code as code,
      Count(Session.id) as count
    FROM
      Session
      JOIN PointDeCharge ON PointDeCharge.id = Session.point_de_charge_id
      JOIN Station ON Station.id = PointDeCharge.station_id
      JOIN OperationalUnit ON OperationalUnit.id = Station.operational_unit_id
    WHERE
      Session.start >= '$from_date'
      AND Session.start < '$to_date'
    GROUP BY
      OperationalUnit.code
    ORDER BY
      OperationalUnit.code
    """
)

OPERATIONAL_UNIT_SESSIONS_FOR_A_DAY_TEMPLATE = Template(
    """
    SELECT
      Amenageur.nom_amenageur as entity,
      Amenageur.siren_amenageur as siren,
      OperationalUnit.code as code,
      Station.id_station_itinerance as id_station_itinerance,
      PointDeCharge.id_pdc_itinerance as id_pdc_itinerance,
      PointDeCharge.puissance_nominale as max_power,
      Session.id as session_id,
      Session.start as "from",
      Session.end as to,
      Session.energy as energy
    FROM
      Session
      JOIN PointDeCharge ON PointDeCharge.id = Session.point_de_charge_id
      JOIN Station ON Station.id = PointDeCharge.station_id
      JOIN OperationalUnit ON OperationalUnit.id = Station.operational_unit_id
      JOIN Amenageur ON Amenageur.id = Station.amenageur_id
    WHERE
      OperationalUnit.code = '$operational_unit_code'
      AND Session.start >= '$from_date'
      AND Session.start < '$to_date'
    ORDER BY
      PointDeCharge.id_pdc_itinerance,
      Session.start,
      Session.end
    """
)


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


@task
def filter_sessions(sessions: pd.DataFrame) -> pd.DataFrame:
    """Clean sent sessions.

    Tasks:
    - Remove duplicates
    - Remove aberrant sessions
    """
    # TODO
    print(sessions)
    return sessions


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
    sessions = filter_sessions(sessions)
    save_tiruert(sessions, environment, from_date, to_date)


@flow
def tiruert_for_period(environment: Environment, from_date: date, to_date: date):
    """Calculate the TIRUERT for a defined period."""
    operational_units = get_operational_units_for_period(
        environment, from_date, to_date
    )
    for code in operational_units[["code"]]:
        tiruert_for_period_and_operational_unit(environment, from_date, to_date, code)
