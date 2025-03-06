"""QualiCharge prefect indicators: infrastructure.

T8: the number of stations by operator.
"""

from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd
from prefect import flow, runtime, task
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy.orm import Session

from indicators.conf import settings
from indicators.db import get_api_db_engine
from indicators.models import IndicatorTimeSpan, Level
from indicators.types import Environment
from indicators.utils import (
    export_indicators,
    get_num_for_level_query_params,
    get_targets_for_level,
)

NUM_POCS_BY_OPERATOR_FOR_LEVEL_QUERY_TEMPLATE = """
SELECT
    count(id_station_itinerance) AS value,
    nom_operateur AS category,
    $level_id AS level_id
FROM
    Station
    INNER JOIN Localisation ON localisation_id = Localisation.id
    INNER JOIN City ON code_insee_commune = City.code
    INNER JOIN Operateur ON Station.operateur_id = operateur.id
    $join_extras
WHERE
    $level_id IN ($indexes)
GROUP BY
    $level_id,
    category
"""
QUERY_NATIONAL_TEMPLATE = """
SELECT
    COUNT(id_station_itinerance) AS value,
    nom_operateur AS category
FROM
    Station
    INNER JOIN Operateur ON Station.operateur_id = operateur.id
GROUP BY
    category
"""


@task(task_run_name="values-for-target-{level:02d}")
def get_values_for_targets(
    level: Level, indexes: List[UUID], environment: Environment
) -> pd.DataFrame:
    """Fetch stations per operator given input level and target index."""
    query_template = Template(NUM_POCS_BY_OPERATOR_FOR_LEVEL_QUERY_TEMPLATE)
    query_params = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= get_num_for_level_query_params(level)
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="t8-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def t8_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    environment: Environment,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate t8 for a level."""
    if level == Level.NATIONAL:
        return t8_national(timespan, environment)
    targets = get_targets_for_level(level, environment)
    ids = targets["id"]
    chunks = (
        np.array_split(ids, int(len(ids) / chunk_size))
        if len(ids) > chunk_size
        else [ids.to_numpy()]
    )
    futures = [
        get_values_for_targets.submit(level, chunk, environment)  # type: ignore[call-overload]
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
        "code": "t8",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": merged["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="t8-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def t8_national(timespan: IndicatorTimeSpan, environment: Environment) -> pd.DataFrame:
    """Calculate t8 at the national level."""
    with Session(get_api_db_engine(environment)) as session:
        res = pd.read_sql_query(QUERY_NATIONAL_TEMPLATE, con=session.connection())
    indicators = {
        "target": None,
        "value": res["value"].fillna(0),
        "code": "t8",
        "level": Level.NATIONAL,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": res["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-t8-{timespan.period.value}",
)
def calculate(  # noqa: PLR0913
    timespan: IndicatorTimeSpan,
    environment: Environment,
    levels: List[Level],
    chunk_size: int = 1000,
    create_artifact: bool = False,
    persist: bool = False,
) -> pd.DataFrame:
    """Run all t8 subflows."""
    subflows_results = [
        t8_for_level(level, timespan, environment, chunk_size=chunk_size)
        for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"t8 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    export_indicators(
        indicators, environment, flow_name, description, create_artifact, persist
    )
    return indicators
