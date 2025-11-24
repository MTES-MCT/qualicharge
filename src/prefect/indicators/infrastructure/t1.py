"""QualiCharge prefect indicators: infrastructure.

T1: the number of publicly open points of charge by power level.
"""

from datetime import datetime
from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd
from prefect import flow, runtime, task
from prefect.futures import wait
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
)

HISTORY_STRATEGY_FIELD: str = "mean"
NUM_POCS_BY_POWER_RANGE_FOR_LEVEL_QUERY_TEMPLATE = """
WITH
    $power_range
SELECT
    COUNT(DISTINCT id_pdc_itinerance) AS value,
    category,
    $level_id AS level_id
FROM
    Statique
    INNER JOIN City ON code_insee_commune = City.code
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
    COUNT(DISTINCT id_pdc_itinerance) AS value,
    category
FROM
    Statique
    LEFT JOIN puissance ON puissance_nominale::numeric <@ category
GROUP BY
    category
ORDER BY
    value DESC
"""


@task(task_run_name="values-for-target-{level:02d}")
def get_values_for_targets(
    level: Level, indexes: List[UUID], environment: Environment
) -> pd.DataFrame:
    """Fetch points of charge per power level given input level and target index."""
    query_template = Template(NUM_POCS_BY_POWER_RANGE_FOR_LEVEL_QUERY_TEMPLATE)
    query_params = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= POWER_RANGE_CTE
    query_params |= get_num_for_level_query_params(level)
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )


@flow(
    flow_run_name="t1-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def t1_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    environment: Environment,
    chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate t1 for a level."""
    if level == Level.NATIONAL:
        return t1_national(timespan, environment)
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
        "code": "t1",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": merged["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    flow_run_name="t1-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def t1_national(timespan: IndicatorTimeSpan, environment: Environment) -> pd.DataFrame:
    """Calculate t1 at the national level."""
    query_template = Template(QUERY_NATIONAL_TEMPLATE)
    query_params = POWER_RANGE_CTE
    with Session(get_api_db_engine(environment)) as session:
        result = pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )
    indicators = {
        "target": "00",
        "value": result["value"].fillna(0),
        "code": "t1",
        "level": Level.NATIONAL,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": result["category"].astype("str"),
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    flow_run_name="meta-t1-{period.value}",
)
def t1(  # noqa: PLR0913
    environment: Environment,
    levels: List[Level],
    start: datetime | None = None,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    chunk_size: int = 1000,
    create_artifact: bool = False,
    persist: bool = False,
) -> pd.DataFrame:
    """Run all t1 subflows."""
    start = datetime.now() if start is None else get_period_start_from_pit(start)
    timespan = IndicatorTimeSpan(period=period, start=start)
    subflows_results = [
        t1_for_level(level, timespan, environment, chunk_size=chunk_size)
        for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"t1 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    export_indicators(
        indicators, environment, flow_name, description, create_artifact, persist
    )
    return indicators
