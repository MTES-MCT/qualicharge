"""QualiCharge prefect indicators: infrastructure.

I7: installed power.
"""

from datetime import datetime
from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd  # type: ignore
from prefect import flow, runtime, task
from prefect.artifacts import create_markdown_artifact
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..conf import settings
from ..models import Indicator, IndicatorPeriod, Level
from ..utils import (
    get_database_engine,
    get_num_for_level_query_params,
    get_targets_for_level,
)

SUM_POWER_FOR_LEVEL_QUERY_TEMPLATE = """
        SELECT
            sum(puissance_nominale) AS value,
            $level_id AS level_id
        FROM
            pointdecharge
            INNER JOIN station ON station.id = station_id
            INNER JOIN localisation ON localisation_id = localisation.id
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
    query_params: dict = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= get_num_for_level_query_params(level)
    return pd.read_sql_query(query_template.substitute(query_params), con=connection)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i7-{period.value}-{level:02d}-{at:%y-%m-%d}",
)
def i7_for_level(
    level: Level,
    period: IndicatorPeriod,
    at: datetime,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate i7 for a level."""
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
        "period": period,
        "timestamp": at,
        "category": None,
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i7-{period.value}-00-{at:%y-%m-%d}",
)
def i7_national(period: IndicatorPeriod, at: datetime) -> pd.DataFrame:
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
                period=period,
                value=count,
                timestamp=at,
            ).model_dump(),
        ]
    )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-i7-{period.value}",
)
def calculate(
    period: IndicatorPeriod, create_artifact: bool = False, chunk_size: int = 1000
) -> List[Indicator]:
    """Run all i7 subflows."""
    now = pd.Timestamp.now()
    subflows_results = [
        i7_national(period, now),
        i7_for_level(Level.REGION, period, now, chunk_size=chunk_size),
        i7_for_level(Level.DEPARTMENT, period, now, chunk_size=chunk_size),
        i7_for_level(Level.EPCI, period, now, chunk_size=chunk_size),
        i7_for_level(Level.CITY, period, now, chunk_size=chunk_size),
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)

    if create_artifact:
        create_markdown_artifact(
            key=runtime.flow_run.name,
            markdown=indicators.to_markdown(),
            description=f"i7 report at {now} (period: {period.value})",
        )

    return [Indicator(**record) for record in indicators.to_dict(orient="records")]  # type: ignore[misc]
