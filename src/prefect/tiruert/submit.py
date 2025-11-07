"""Tiruert submission flows.

This is the core part that handles TIRUERT calculation for a quarter
and CARBURE API integration.
"""

from datetime import date, datetime
from string import Template
from typing import List

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from prefect import flow, task
from prefect.client.schemas.objects import StateType
from prefect.states import Completed, Failed
from sqlalchemy import text
from sqlalchemy.orm import Session

from indicators.db import get_api_db_engine, get_indicators_db_engine
from indicators.models import IndicatorPeriod, Level
from indicators.types import Environment
from indicators.utils import export_indicators

from .carbure import CarbureAPISettings, CarbureClient

ENERGY_BY_STATION_TEMPLATE = Template(
    """
    WITH
      energy_over_period AS (
        SELECT
          jsonb_path_query(extras, '$$.entity') ->> 0 as entity,
          jsonb_path_query(extras, '$$.siren') ->> 0 AS siren,
          target as code,
          jsonb_path_query(extras, '$$.id_station_itinerance') ->> 0 AS station,
          jsonb_path_query(extras, '$$.energy')::NUMERIC AS energy
        FROM
          $environment
        WHERE
          code = 'tirue'
          AND period = 'd'
          AND (extras @> '[{"siren": "$siren"}]')
          AND timestamp >= '$from_date'
          AND timestamp < '$to_date'
      )
    SELECT
      entity,
      siren,
      code,
      station,
      sum(energy) / 1000. AS energy_mwh
    FROM
      energy_over_period
    GROUP BY
      entity,
      siren,
      code,
      station
    ORDER BY
      siren,
      code,
      station
    """
)


@task
def get_amenageurs_siren(environment: Environment) -> List[str]:
    """Get distinct amenageurs SIREN for an environment."""
    with Session(get_api_db_engine(environment)) as session:
        results = session.execute(
            text(
                """
                SELECT DISTINCT
                  siren_amenageur
                FROM
                  Amenageur
                ORDER BY
                  siren_amenageur
                """
            )
        )
    return [row[0] for row in results.all()]


@task
def extract(
    environment: Environment, from_date: date, to_date: date, siren: str
) -> pd.DataFrame:
    """Aggregate daily calculation for a period and an amenageur."""
    with Session(get_indicators_db_engine()) as session:
        return pd.read_sql_query(
            ENERGY_BY_STATION_TEMPLATE.substitute(
                {
                    "environment": environment.value,
                    "siren": siren,
                    "from_date": from_date,
                    # to_date is excluded in the request
                    "to_date": to_date + relativedelta(days=1),
                }
            ),
            con=session.connection(),
        )


@task
def transform(
    environment: Environment,
    from_date: date,
    to_date: date,
    siren: str,
    energy_by_station: pd.DataFrame,
) -> List[dict]:
    """Prepare monthly volumes by amenageur for carbure."""
    # Add missing columns and rename columns as expected by the CARBURE API
    energy_by_station["from"] = from_date
    energy_by_station["to"] = to_date
    energy_by_station["is_controlled"] = False
    energy_by_station.rename(
        columns={"station": "id", "energy_mwh": "energy"}, inplace=True
    )

    # Prepare the payload to save and submit
    payload = []
    by_entity = energy_by_station.groupby(["entity", "siren"])
    for entity_group in by_entity.groups:
        entity, siren = entity_group
        entity_payload = {"entity": entity, "siren": siren, "operational_units": []}
        by_code = by_entity.get_group(entity_group).groupby(["code", "from", "to"])
        for code_group in by_code.groups:
            code, from_, to_ = code_group
            by_stations = by_code.get_group(code_group)
            code_payload = {
                "code": code,
                "from": str(from_),
                "to": str(to_),
                "stations": by_stations[["id", "energy", "is_controlled"]].to_dict(
                    orient="records"
                ),
            }
            entity_payload["operational_units"].append(code_payload)
        payload.append(entity_payload)

    return payload


@task
def load(
    environment: Environment,
    siren: str,
    total: float,
    from_date: date,
    payload: List[dict],
):
    """Save monthly indicator for CARBURE."""
    # Save energy volume
    indicators = pd.DataFrame(
        {
            "target": siren,
            # total for period in MWh
            "value": total,
            "code": "tirue",
            "level": Level.AMENAGEUR,
            "period": IndicatorPeriod.MONTH,
            "timestamp": datetime.combine(from_date, datetime.min.time()).isoformat(),
            "category": None,
            "extras": [
                payload,
            ],
        }
    )

    export_indicators(
        indicators=indicators,
        environment=environment,
        flow_name="tiruert-for-month-and-amenageur",
        description=(
            "Cumulated sessions per station over a month for TIRUERT calculation."
        ),
        create_artifact=False,
        persist=True,
    )


@task
def submit(payload: List[dict], siren: str, from_date: date):
    """Submit payload to CARBURE."""
    carbure_config = CarbureAPISettings()
    client = CarbureClient(carbure_config)

    try:
        client.bulk_create_certificates(payload)
    except requests.HTTPError:
        return Failed(
            message=(
                f"CARBURE submission failed for amenageur {siren} (date: {from_date})"
            )
        )
    return Completed(
        message=f"Monthly volumes sent for amenageur {siren} (date: {from_date})"
    )


@flow
def tiruert_for_month_and_amenageur(
    environment: Environment, year: int, month: int, siren: str
):
    """Handle TIRUERT for an amenageur and a target month."""
    from_date = date(year=year, month=month, day=1)
    to_date = from_date + relativedelta(months=1) + relativedelta(days=-1)

    energy_by_station = extract(environment, from_date, to_date, siren)
    payload = transform(environment, from_date, to_date, siren, energy_by_station)
    state = submit(payload, siren, from_date)

    # Only save indicator if submission is successful
    if state.type == StateType.FAILED:
        return

    load(environment, siren, energy_by_station["energy"].sum(), from_date, payload)


@flow
def tiruert_for_month(environment: Environment, year: int, month: int):
    """Handle TIRUERT for an amenageur and a target month."""
    for siren in get_amenageurs_siren(environment):
        tiruert_for_month_and_amenageur(environment, year, month, siren)
