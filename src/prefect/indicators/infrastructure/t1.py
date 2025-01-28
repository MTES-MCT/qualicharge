"""QualiCharge prefect indicators: infrastructure.

T1: the number of publicly open points of charge by power level.
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
)

NUM_POCS_BY_POWER_RANGE_FOR_LEVEL_QUERY_TEMPLATE = """
        WITH
            $power_range
        SELECT
            COUNT(DISTINCT PointDeCharge.id_pdc_itinerance) AS value,
            category,
            $level_id AS level_id
        FROM
            PointDeCharge
            INNER JOIN Station ON PointDeCharge.station_id = Station.id
            INNER JOIN Localisation ON Station.localisation_id = Localisation.id
            INNER JOIN City ON Localisation.code_insee_commune = City.code
            LEFT JOIN puissance ON puissance_nominale::numeric <@ category
            $join_extras
        WHERE
            $level_id IN ($indexes)
        GROUP BY
            $level_id,
            category
        ORDER BY
            value DESC
        """
QUERY_NATIONAL_TEMPLATE = """
        WITH
            $power_range
        SELECT
            COUNT(DISTINCT PointDeCharge.id_pdc_itinerance) AS value,
            category
        FROM
            PointDeCharge
            LEFT JOIN puissance ON puissance_nominale::numeric <@ category
        GROUP BY
            category
        ORDER BY
            value DESC
        """


@task(task_run_name="values-for-target-{level:02d}")
def get_values_for_targets(
    connection: Connection, level: Level, indexes: List[UUID]
) -> pd.DataFrame:
    """Fetch points of charge per power level given input level and target index."""
    query_template = Template(NUM_POCS_BY_POWER_RANGE_FOR_LEVEL_QUERY_TEMPLATE)
    query_params = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= POWER_RANGE_CTE
    query_params |= get_num_for_level_query_params(level)
    return pd.read_sql_query(query_template.substitute(query_params), con=connection)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="t1-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def t1_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate t1 for a level."""
    if level == Level.NATIONAL:
        return t1_national(timespan)
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
            get_values_for_targets.submit(connection, level, chunk)  # type: ignore[call-overload]
            for chunk in chunks
        ]
        wait(futures)

    # Concatenate results and serialize indicators
    results = pd.concat([future.result() for future in futures], ignore_index=True)
    merged = targets.merge(results, how="right", left_on="id", right_on="level_id")

    # Build result DataFrame
    indicators = {
        "target": merged["code"],
        "value": merged["value"].fillna(0),
        "code": "t1",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": merged["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="t1-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def t1_national(timespan: IndicatorTimeSpan) -> pd.DataFrame:
    """Calculate t1 at the national level."""
    engine = get_database_engine()
    query_template = Template(QUERY_NATIONAL_TEMPLATE)
    query_params = POWER_RANGE_CTE
    with engine.connect() as connection:
        # result = pd.read_sql_query(QUERY_NATIONAL, con=connection)
        res = pd.read_sql_query(query_template.substitute(query_params), con=connection)
    indicators = {
        "target": None,
        "value": res["value"].fillna(0),
        "code": "t1",
        "level": Level.NATIONAL,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": res["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-t1-{timespan.period.value}",
)
def calculate(
    timespan: IndicatorTimeSpan,
    levels: List[Level],
    create_artifact: bool = False,
    chunk_size: int = 1000,
    format_pd: bool = False,
) -> List[Indicator]:
    """Run all t1 subflows."""
    subflows_results = [
        t1_for_level(level, timespan, chunk_size=chunk_size) for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"t1 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    return export_indic(indicators, create_artifact, flow_name, description, format_pd)
