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
from prefect.cache_policies import NONE
from prefect.futures import wait
from sqlalchemy import text
from sqlalchemy.orm import Session

from indicators.conf import settings
from indicators.db import get_api_db_engine
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level
from indicators.types import Environment
from indicators.utils import (
    export_indicators,
    get_num_for_level_query_params,
    get_period_start_from_pit,
    get_targets_for_level,
)

HISTORY_STRATEGY_FIELD: str = "mean"
SUM_POWER_FOR_LEVEL_QUERY_TEMPLATE = """
SELECT
    sum(puissance_nominale) AS value,
    $level_id AS level_id
FROM
    statique
    INNER JOIN city on city.code = code_insee_commune
    $join_extras
WHERE $level_id IN ($indexes)
GROUP BY $level_id
ORDER BY value DESC
"""


@task(task_run_name="values-for-target-{level:02d}", cache_policy=NONE)
def get_values_for_targets(
    level: Level, indexes: List[UUID], environment: Environment
) -> pd.DataFrame:
    """Fetch points of charge given input level and target index."""
    query_template = Template(SUM_POWER_FOR_LEVEL_QUERY_TEMPLATE)
    query_params = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= get_num_for_level_query_params(level)
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )


@flow(
    flow_run_name="i7-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def i7_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    environment: Environment,
    chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate i7 for a level."""
    if level == Level.NATIONAL:
        return i7_national(timespan, environment)
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
        "code": "i7",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": None,
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    flow_run_name="i7-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def i7_national(timespan: IndicatorTimeSpan, environment: Environment) -> pd.DataFrame:
    """Calculate i7 at the national level."""
    with Session(get_api_db_engine(environment)) as session:
        result = session.execute(
            text("SELECT sum(puissance_nominale) FROM pointdecharge")
        )
        count = result.one()[0]
    indicators = {
        "target": "00",
        "value": [count],
        "code": "i7",
        "level": Level.NATIONAL,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": None,
        "extras": None,
    }
    return pd.DataFrame(indicators)


@flow(
    flow_run_name="meta-i7-{period.value}",
)
def calculate(  # noqa: PLR0913
    environment: Environment,
    levels: List[Level],
    start: datetime | None = None,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    chunk_size: int = 1000,
    create_artifact: bool = False,
    persist: bool = False,
) -> pd.DataFrame:
    """Run all i7 subflows."""
    start = datetime.now() if start is None else get_period_start_from_pit(start)
    timespan = IndicatorTimeSpan(period=period.value, start=start)
    subflows_results = [
        i7_for_level(level, timespan, environment, chunk_size=chunk_size)
        for level in levels
    ]
    indicators = pd.concat(
        [res.astype(subflows_results[0].dtypes) for res in subflows_results],
        ignore_index=True,
    )
    description = f"i7 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    export_indicators(
        indicators, environment, flow_name, description, create_artifact, persist
    )

    return indicators
