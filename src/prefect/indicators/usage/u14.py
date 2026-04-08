"""QualiCharge prefect indicators: usage.

U14: energy by unit code and by delivery (direct/indirect, AC/DC, valid/invalid PDL).
"""

from datetime import datetime
from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd  # type: ignore
from prefect import flow, runtime, task
from prefect.futures import wait
from sqlalchemy.orm import Session

from indicators.conf import settings
from indicators.db import get_api_db_engine
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level
from indicators.types import Environment
from indicators.utils import (
    ALIMENTATION,
    IS_DC,
    IS_VALID_PDL,
    export_indicators,
    get_num_for_level_query_params,
    get_period_start_from_pit,
    get_targets_for_level,
    get_timespan_filter_query_params,
)

HISTORY_STRATEGY_FIELD: str = "mean"
ENERGY_BY_DELIVERY_TEMPLATE = """
WITH
  Stations AS (
    SELECT
      Station.id,
      operational_unit_id,
      code_insee_commune,
      raccordement = 'Direct' AS is_direct,
      $is_valid_pdl AS is_valid_pdl,
      $is_dc AS is_dc
    FROM
      Pointdecharge
      LEFT JOIN Station ON Station.id = station_id
      LEFT JOIN Localisation ON Localisation.id = localisation_id
    GROUP BY
      station.id,
      code_insee_commune,
      operational_unit_id,
      is_direct,
      is_valid_pdl
  ),
  Statiques AS (
    SELECT
      code,
      $alimentation AS alimentation,
      Pointdecharge.id AS pdc_id,
      code_insee_commune,
      puissance_nominale
    FROM
      Pointdecharge
      LEFT JOIN Stations ON stations.id = station_id
      LEFT JOIN Operationalunit ON operational_unit_id = Operationalunit.id
  ),
  Sessions_uniques AS (
    SELECT
      max(energy) AS max_energy_kwh,
      point_de_charge_id
    FROM
      SESSION
      INNER JOIN Statiques ON point_de_charge_id = Statiques.pdc_id
    WHERE
      $timespan
      AND energy < 1.1 * puissance_nominale * EXTRACT(
          EPOCH FROM (Session.end - Session.start)
        ) / 3600
    GROUP BY
      START,
      SESSION.end,
      point_de_charge_id
  )
SELECT
  $level_id AS level_id,
  alimentation AS category,
  sum(max_energy_kwh) AS VALUE
FROM
  Sessions_uniques
  INNER JOIN Statiques ON point_de_charge_id = Statiques.pdc_id
  $join_extras
WHERE
    $level_id IN ($indexes)
GROUP BY
  $level_id,
  category
"""

QUERY_NATIONAL_TEMPLATE = """
WITH
  Stations AS (
    SELECT
      Station.id,
      id_station_itinerance,
      operational_unit_id,
      code_insee_commune,
      raccordement = 'Direct' AS is_direct,
      $is_valid_pdl AS is_valid_pdl,
      $is_dc AS is_dc
    FROM
      Pointdecharge
      LEFT JOIN Station ON Station.id = station_id
      LEFT JOIN Localisation ON Localisation.id = localisation_id
    GROUP BY
      Station.id,
      id_station_itinerance,
      code_insee_commune,
      operational_unit_id,
      is_direct,
      is_valid_pdl
  ),
  Statiques AS (
    SELECT
      $alimentation AS alimentation,
      Pointdecharge.id AS pdc_id,
      station_id,
      puissance_nominale
    FROM
      Pointdecharge
      LEFT JOIN Stations ON stations.id = station_id
  ),
  Sessions_uniques AS (
    SELECT
      max(energy) AS max_energy_kwh,
      point_de_charge_id
    FROM
      SESSION
      INNER JOIN Statiques ON point_de_charge_id = Statiques.pdc_id
    WHERE
      $timespan
      AND energy < 1.1 * puissance_nominale * EXTRACT(
          EPOCH FROM (Session.end - Session.start)
        ) / 3600
    GROUP BY
      START,
      SESSION.end,
      point_de_charge_id
  )
SELECT
  alimentation AS category,
  sum(max_energy_kwh) AS VALUE
FROM
  Sessions_uniques
  INNER JOIN Statiques ON point_de_charge_id = Statiques.pdc_id
GROUP BY
  category
"""


@task(task_run_name="values-for-target-{level:02d}")
def get_values_for_targets(
    level: Level,
    timespan: IndicatorTimeSpan,
    indexes: List[UUID],
    environment: Environment,
) -> pd.DataFrame:
    """Fetch sessions given input level, timestamp and target index."""
    query_template = Template(ENERGY_BY_DELIVERY_TEMPLATE)
    query_params = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= IS_VALID_PDL | IS_DC | ALIMENTATION
    query_params |= get_num_for_level_query_params(level)
    query_params |= get_timespan_filter_query_params(timespan, session=True)
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )


@flow(
    flow_run_name="u14-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def u14_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    environment: Environment,
    chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate u14 for a level and a timestamp."""
    if level == Level.NATIONAL:
        return u14_national(timespan, environment)
    targets = get_targets_for_level(level, environment)
    ids = targets["id"]
    chunks = (
        np.array_split(ids, int(len(ids) / chunk_size))
        if len(ids) > chunk_size
        else [ids.to_numpy()]
    )
    futures = [
        get_values_for_targets.submit(level, timespan, chunk, environment)  # type: ignore[call-overload]
        for chunk in chunks
    ]
    wait(futures)

    # Concatenate results and serialize indicators
    results = pd.concat([future.result() for future in futures], ignore_index=True)
    merged = targets.merge(results, how="left", left_on="id", right_on="level_id")

    # Build result DataFrame
    indicators = {
        "target": merged["code"],
        "value": merged["value"].fillna(0),
        "code": "u14",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": merged["category"],
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    flow_run_name="u14-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def u14_national(timespan: IndicatorTimeSpan, environment: Environment) -> pd.DataFrame:
    """Calculate u14 at the national level."""
    query_template = Template(QUERY_NATIONAL_TEMPLATE)
    query_params = get_timespan_filter_query_params(timespan, session=True)
    query_params |= IS_VALID_PDL | IS_DC | ALIMENTATION
    with Session(get_api_db_engine(environment)) as session:
        result = pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )
    indicators = {
        "target": "00",
        "value": result["value"].fillna(0),
        "code": "u14",
        "level": Level.NATIONAL,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": result["category"],
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    flow_run_name="meta-u14-{period.value}",
)
def u14(  # noqa: PLR0913
    environment: Environment,
    levels: List[Level],
    start: datetime | None = None,
    offset: int = -1,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    chunk_size: int = 1000,
    create_artifact: bool = False,
    persist: bool = False,
) -> pd.DataFrame:
    """Run all u14 subflows."""
    start = (
        datetime.now()
        if not offset and start is None
        else get_period_start_from_pit(start, offset, period)
    )
    timespan = IndicatorTimeSpan(period=period, start=start)
    subflows_results = [
        u14_for_level(level, timespan, environment, chunk_size=chunk_size)
        for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"u14 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    export_indicators(
        indicators, environment, flow_name, description, create_artifact, persist
    )
    return indicators
