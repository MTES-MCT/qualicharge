"""QualiCharge prefect indicators: usage.

U6: session duration by power category.
"""

from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd  # type: ignore
from prefect import flow, runtime, task
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy.engine import Connection

from ..conf import settings
from ..models import Indicator, IndicatorTimeSpan, Level
from ..utils import (
    POWER_RANGE_CTE,
    export_indic,
    get_database_engine,
    get_num_for_level_query_params,
    get_targets_for_level,
    get_timespan_filter_query_params,
)

DURATION_FOR_LEVEL_QUERY_TEMPLATE = """
        WITH
            $power_range,
            sessionf AS (
                SELECT
                    point_de_charge_id,
                    sum(session.end -session.start) as duree_pdc
                FROM
                    session
                WHERE
                    $timespan
                GROUP BY
                    point_de_charge_id
            )
        SELECT
            extract ('epoch' from sum(duree_pdc)) / 3600.0 AS value,
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
                    sum(session.end -session.start) as duree_pdc
                FROM
                    session
                WHERE
                    $timespan
                GROUP BY
                    point_de_charge_id
            )
        SELECT
            extract ('epoch' from sum(duree_pdc)) / 3600.0 AS value,
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
    connection: Connection,
    level: Level,
    timespan: IndicatorTimeSpan,
    indexes: List[UUID],
) -> pd.DataFrame:
    """Fetch sessions given input level, timestamp and target index."""
    query_template = Template(DURATION_FOR_LEVEL_QUERY_TEMPLATE)
    query_params = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= POWER_RANGE_CTE
    query_params |= get_num_for_level_query_params(level)
    query_params |= get_timespan_filter_query_params(timespan, session=True)
    return pd.read_sql_query(query_template.substitute(query_params), con=connection)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="u6-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def u6_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate u6 for a level and a timestamp."""
    if level == Level.NATIONAL:
        return u6_national(timespan)
    engine = get_database_engine()
    with engine.connect() as connection:
        targets = get_targets_for_level(connection, level)
        ids = targets["id"]
        chunks = (
            np.array_split(ids, int(len(ids) / chunk_size))
            if len(ids) > chunk_size
            else [ids.to_numpy()]
        )
        futures = [
            get_values_for_targets.submit(connection, level, timespan, chunk)  # type: ignore[call-overload]
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
        "code": "u6",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": merged["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="u6-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def u6_national(timespan: IndicatorTimeSpan) -> pd.DataFrame:
    """Calculate u6 at the national level."""
    engine = get_database_engine()
    query_template = Template(QUERY_NATIONAL_TEMPLATE)
    query_params = get_timespan_filter_query_params(timespan, session=True)
    query_params |= POWER_RANGE_CTE
    with engine.connect() as connection:
        res = pd.read_sql_query(query_template.substitute(query_params), con=connection)
    indicators = {
        "target": None,
        "value": res["value"].fillna(0),
        "code": "u6",
        "level": Level.NATIONAL,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": res["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-u6-{timespan.period.value}",
)
def calculate(
    timespan: IndicatorTimeSpan,
    levels: List[Level],
    create_artifact: bool = False,
    chunk_size: int = 1000,
    format_pd: bool = False,
) -> List[Indicator]:
    """Run all u6 subflows."""
    subflows_results = [
        u6_for_level(level, timespan, chunk_size=chunk_size) for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"u6 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    return export_indic(indicators, create_artifact, flow_name, description, format_pd)
