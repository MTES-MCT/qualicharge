"""QualiCharge prefect indicators: usage.

U9: energy by power category.
"""

from datetime import datetime
from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd  # type: ignore
from prefect import flow, runtime, task
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy.orm import Session

from indicators.conf import settings
from indicators.db import get_api_db_engine
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level
from indicators.types import Environment
from indicators.utils import (
    POWER_RANGE_CTE,
    export_indicators,
    get_num_for_level_query_params,
    get_period_start_from_pit,
    get_targets_for_level,
    get_timespan_filter_query_params,
)

HISTORY_STRATEGY_FIELD: str = "mean"
ENERGY_FOR_LEVEL_QUERY_TEMPLATE = """
        WITH
            $power_range,
            sessionf AS (
                SELECT
                    point_de_charge_id,
                    sum(energy) as energy_pdc
                FROM
                    session
                WHERE
                    $timespan
                GROUP BY
                    point_de_charge_id
            )
        SELECT
            sum(energy_pdc) AS value,
            category,
            $level_id AS level_id
        FROM
            sessionf
            INNER JOIN statique ON point_de_charge_id = pdc_id
            --INNER JOIN PointDeCharge ON sessionf.point_de_charge_id = PointDeCharge.id
            --LEFT JOIN Station ON station_id = Station.id
            --LEFT JOIN Localisation ON localisation_id = Localisation.id
            LEFT JOIN City ON City.code = code_insee_commune
            LEFT JOIN puissance ON puissance_nominale::numeric <@ category
            $join_extras
        WHERE
            $level_id IN ($indexes)
        GROUP BY
            $level_id,
            category
        """

QUERY_NATIONAL_TEMPLATE = """
        WITH
            $power_range,
            sessionf AS (
                SELECT
                    point_de_charge_id,
                    sum(energy) as energy_pdc
                FROM
                    session
                WHERE
                    $timespan
                GROUP BY
                    point_de_charge_id
            )
        SELECT
            sum(energy_pdc) AS value,
            category
        FROM
            sessionf
            INNER JOIN statique ON point_de_charge_id = pdc_id
            --INNER JOIN PointDeCharge ON sessionf.point_de_charge_id = PointDeCharge.id
            LEFT JOIN puissance ON puissance_nominale::numeric <@ category
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
    query_template = Template(ENERGY_FOR_LEVEL_QUERY_TEMPLATE)
    query_params = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= POWER_RANGE_CTE
    query_params |= get_num_for_level_query_params(level)
    query_params |= get_timespan_filter_query_params(timespan, session=True)
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="u9-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def u9_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    environment: Environment,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate u9 for a level and a timestamp."""
    if level == Level.NATIONAL:
        return u9_national(timespan, environment)
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
        "code": "u9",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": merged["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="u9-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def u9_national(timespan: IndicatorTimeSpan, environment: Environment) -> pd.DataFrame:
    """Calculate u9 at the national level."""
    query_template = Template(QUERY_NATIONAL_TEMPLATE)
    query_params = get_timespan_filter_query_params(timespan, session=True)
    query_params |= POWER_RANGE_CTE
    with Session(get_api_db_engine(environment)) as session:
        result = pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )
    indicators = {
        "target": "00",
        "value": result["value"].fillna(0),
        "code": "u9",
        "level": Level.NATIONAL,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": result["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-u9-{period.value}",
)
def calculate(  # noqa: PLR0913
    environment: Environment,
    levels: List[Level],
    start: datetime | None = None,
    offset: int = -1,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    chunk_size: int = 1000,
    create_artifact: bool = False,
    persist: bool = False,
) -> pd.DataFrame:
    """Run all u9 subflows."""
    start = (
        datetime.now()
        if not offset and start is None
        else get_period_start_from_pit(start, offset, period)
    )
    timespan = IndicatorTimeSpan(period=period.value, start=start)
    subflows_results = [
        u9_for_level(level, timespan, environment, chunk_size=chunk_size)
        for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"u9 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    export_indicators(
        indicators, environment, flow_name, description, create_artifact, persist
    )
    return indicators
