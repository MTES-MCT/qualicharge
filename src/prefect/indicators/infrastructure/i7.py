"""QualiCharge prefect indicators: infrastructure.

I7: installed power.
"""

from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd  # type: ignore
from prefect import flow, runtime, task
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..conf import settings
from ..models import Indicator, IndicatorTimeSpan, Level
from ..utils import (
    export_indic,
    get_database_engine,
    get_num_for_level_query_params,
    get_targets_for_level,
)

SUM_POWER_FOR_LEVEL_QUERY_TEMPLATE = """
        SELECT
            sum(puissance_nominale) AS value,
            $level_id AS level_id
        FROM
            statique
            --pointdecharge
            --INNER JOIN station ON station.id = station_id
            --INNER JOIN localisation ON localisation_id = localisation.id
            INNER JOIN city on city.code = code_insee_commune
            $join_extras
        WHERE $level_id IN ($indexes)
        GROUP BY $level_id
        ORDER BY value DESC
        """


@task(task_run_name="values-for-target-{level:02d}")
def get_values_for_targets(
    connection: Connection, level: Level, indexes: List[UUID]
) -> pd.DataFrame:
    """Fetch pdc given input level and target index."""
    query_template = Template(SUM_POWER_FOR_LEVEL_QUERY_TEMPLATE)
    query_params = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= get_num_for_level_query_params(level)
    return pd.read_sql_query(query_template.substitute(query_params), con=connection)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i7-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def i7_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate i7 for a level."""
    if level == Level.NATIONAL:
        return i7_national(timespan)
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
    merged = targets.merge(results, how="left", left_on="id", right_on="level_id")

    # Build result DataFrame
    indicators = {
        "target": merged["code"],
        "value": merged["value"].fillna(0),
        "code": "i7",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": None,
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i7-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def i7_national(timespan: IndicatorTimeSpan) -> pd.DataFrame:
    """Calculate i7 at the national level."""
    engine = get_database_engine()
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT sum(puissance_nominale) FROM pointdecharge")
        )
        count = result.one()[0]
    return pd.DataFrame.from_records(
        [
            Indicator(
                code="i7",
                level=Level.NATIONAL,
                period=timespan.period,
                value=count,
                timestamp=timespan.start.isoformat(),
            ).model_dump(),
        ]
    )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-i7-{timespan.period.value}",
)
def calculate(
    timespan: IndicatorTimeSpan,
    levels: List[Level],
    create_artifact: bool = False,
    chunk_size: int = 1000,
    format_pd: bool = False,
) -> List[Indicator]:
    """Run all i7 subflows."""
    subflows_results = [
        i7_for_level(level, timespan, chunk_size=chunk_size) for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"i7 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    return export_indic(indicators, create_artifact, flow_name, description, format_pd)
