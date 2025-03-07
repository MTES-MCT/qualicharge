"""QualiCharge prefect indicators: infrastructure.

E4: the list of points of charge in activity.
"""

from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd  # type: ignore
from prefect import flow, runtime, task
from prefect.cache_policies import NONE
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..conf import settings
from ..db import get_api_db_engine
from ..models import Indicator, IndicatorTimeSpan, Level
from ..types import Environment
from ..utils import (
    export_indicators,
    get_num_for_level_query_params,
    get_targets_for_level,
)

LIST_POCS_FOR_LEVEL_QUERY_TEMPLATE = """
SELECT
    id_pdc_itinerance
    $level_id AS level_id
FROM
    SESSION
    INNER JOIN PointDeCharge ON point_de_charge_id = PointDeCharge.id 
    LEFT JOIN station ON station_id = station.id
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city ON city.code = code_insee_commune
    $join_extras
 WHERE
    $level_id IN ($indexes)
    AND START >= $start - interval '30 days' 
    AND START < $start
GROUP BY
    id_pdc_itinerance,
    $level_id
"""


@task(task_run_name="values-for-target-{level:02d}", cache_policy=NONE)
def get_values_for_targets(
    level: Level, indexes: List[UUID], environment: Environment
) -> pd.DataFrame:
    """Fetch points of charge given input level and target index."""
    query_template = Template(NUM_POCS_FOR_LEVEL_QUERY_TEMPLATE)
    query_params: dict = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= get_num_for_level_query_params(level)
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="e4-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def e4_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    environment: Environment,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate e4 for a level."""
    if level == Level.NATIONAL:
        return e4_national(timespan, environment)
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
    merged = targets.merge(results, how="left", left_on="id", right_on="level_id")

    # Build result DataFrame
    indicators = {
        "target": merged["code"],
        "value": merged["value"].fillna(0),
        "code": "e4",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": None,
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="e4-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def e4_national(timespan: IndicatorTimeSpan, environment: Environment) -> pd.DataFrame:
    """Calculate e4 at the national level."""
    with Session(get_api_db_engine(environment)) as session:
        result = session.execute(text("SELECT COUNT(*) FROM PointDeCharge"))
        count = result.one()[0]

    return pd.DataFrame.from_records(
        [
            Indicator(
                code="e4",
                level=Level.NATIONAL,
                period=timespan.period,
                value=count,
                timestamp=timespan.start.isoformat(),
            ).model_dump(),
        ]
    )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-e4-{timespan.period.value}",
)
def calculate(  # noqa: PLR0913
    timespan: IndicatorTimeSpan,
    environment: Environment,
    levels: List[Level],
    chunk_size: int = 1000,
    create_artifact: bool = False,
    persist: bool = False,
) -> pd.DataFrame:
    """Run all e4 subflows."""
    subflows_results = [
        e4_for_level(level, timespan, environment, chunk_size=chunk_size)
        for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"e4 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    export_indicators(
        indicators, environment, flow_name, description, create_artifact, persist
    )
    return indicators
