"""QualiCharge prefect indicators: infrastructure.

I1: the number of publicly open points of charge.
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
    export_indic,
    get_num_for_level_query_params,
    get_targets_for_level,
)

NUM_POCS_FOR_LEVEL_QUERY_TEMPLATE = """
        SELECT
            COUNT(DISTINCT id_pdc_itinerance) AS value,
            $level_id AS level_id
        FROM
            Statique
            INNER JOIN City ON code_insee_commune = City.code
            $join_extras
        WHERE $level_id IN ($indexes)
        GROUP BY $level_id
        """


@task(task_run_name="values-for-target-{level:02d}", cache_policy=NONE)
def get_values_for_targets(
    level: Level, indexes: List[UUID], environment: Environment
) -> pd.DataFrame:
    """Fetch points of charge given input level and target index."""
    query_template = Template(NUM_POCS_FOR_LEVEL_QUERY_TEMPLATE)
    query_params = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= get_num_for_level_query_params(level)
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i1-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def i1_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    environment: Environment,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate i1 for a level."""
    if level == Level.NATIONAL:
        return i1_national(timespan, environment)
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
        "code": "i1",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": None,
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i1-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def i1_national(timespan: IndicatorTimeSpan, environment: Environment) -> pd.DataFrame:
    """Calculate i1 at the national level."""
    with Session(get_api_db_engine(environment)) as session:
        result = session.execute(text("SELECT COUNT(*) FROM PointDeCharge"))
        count = result.one()[0]

    return pd.DataFrame.from_records(
        [
            Indicator(
                code="i1",
                level=Level.NATIONAL,
                period=timespan.period,
                value=count,
                timestamp=timespan.start.isoformat(),
            ).model_dump(),
        ]
    )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-i1-{timespan.period.value}",
)
def calculate(
    timespan: IndicatorTimeSpan,
    environment: Environment,
    levels: List[Level],
    options: dict = {},
    chunk_size: int = 1000,
) -> pd.DataFrame:
    """Run all i1 subflows."""
    opt = {"create-artifact": False, "persist": False} | options
    subflows_results = [
        i1_for_level(level, timespan, environment, chunk_size=chunk_size)
        for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"i1 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    return export_indic(indicators, environment, opt, flow_name, description)
