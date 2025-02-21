"""QualiCharge prefect indicators: infrastructure.

I1: the number of publicly open points of charge.
"""

from datetime import datetime
from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd  # type: ignore
from prefect import flow, runtime, task
from prefect.artifacts import create_markdown_artifact
from prefect.cache_policies import NONE
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..conf import settings
from ..db import get_api_db_engine, save_indicators
from ..models import Indicator, IndicatorPeriod, Level
from ..types import Environment
from ..utils import (
    get_num_for_level_query_params,
    get_targets_for_level,
)

NUM_POCS_FOR_LEVEL_QUERY_TEMPLATE = """
SELECT
    COUNT(DISTINCT PointDeCharge.id_pdc_itinerance) AS value,
    $level_id AS level_id
FROM
    PointDeCharge
    INNER JOIN Station ON PointDeCharge.station_id = Station.id
    INNER JOIN Localisation ON Station.localisation_id = Localisation.id
    INNER JOIN City ON Localisation.code_insee_commune = City.code
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
    query_params: dict = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= get_num_for_level_query_params(level)
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i1-{period.value}-{level:02d}-{at:%y-%m-%d}",
)
def i1_for_level(
    level: Level,
    period: IndicatorPeriod,
    at: datetime,
    environment: Environment,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate i1 for a level."""
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
        "period": period,
        "timestamp": at,
        "category": None,
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i1-{period.value}-00-{at:%y-%m-%d}",
)
def i1_national(
    period: IndicatorPeriod, at: datetime, environment: Environment
) -> pd.DataFrame:
    """Calculate i1 at the national level."""
    with Session(get_api_db_engine(environment)) as session:
        result = session.execute(text("SELECT COUNT(*) FROM PointDeCharge"))
        count = result.one()[0]

    return pd.DataFrame.from_records(
        [
            Indicator(
                code="i1",
                level=Level.NATIONAL,
                period=period,
                value=count,
                timestamp=at,
            ).model_dump(),
        ]
    )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-i1-{period.value}",
)
def calculate(
    period: IndicatorPeriod,
    environment: Environment,
    create_artifact: bool = False,
    persist: bool = False,
    chunk_size: int = 1000,
) -> List[Indicator]:
    """Run all i1 subflows."""
    now = pd.Timestamp.now()
    subflows_results = [
        i1_national(period, now, environment),
        i1_for_level(Level.REGION, period, now, environment, chunk_size=chunk_size),
        i1_for_level(Level.DEPARTMENT, period, now, environment, chunk_size=chunk_size),
        i1_for_level(Level.EPCI, period, now, environment, chunk_size=chunk_size),
        i1_for_level(Level.CITY, period, now, environment, chunk_size=chunk_size),
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)

    if persist and environment:
        save_indicators(environment, indicators)

    if create_artifact:
        create_markdown_artifact(
            key=f"{runtime.flow_run.name}-{environment}",
            markdown=indicators.to_markdown(),
            description=f"i1 report at {now} (period: {period.value})",
        )

    return [Indicator(**record) for record in indicators.to_dict(orient="records")]  # type: ignore[misc]
