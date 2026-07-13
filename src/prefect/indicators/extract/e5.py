"""QualiCharge prefect indicators: extract.

E5: the list of points of charge in activity.

data : id_pdc_itinerance, id_station_itinerance, puissance_nominale, latitude, longitude
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
from sqlalchemy.orm import Session

from indicators.conf import settings
from indicators.db import get_api_db_engine
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level, PeriodDuration
from indicators.types import Environment
from indicators.utils import (
    export_indicators,
    get_num_for_level_query_params,
    get_period_start_from_pit,
    get_targets_for_level,
)

HISTORY_STRATEGY_FIELD: str = "mean"
LIST_POCS_FOR_LEVEL_QUERY_TEMPLATE = """
SELECT
    statique.id_pdc_itinerance,
    statique.id_station_itinerance,
    statique.puissance_nominale,
    ST_X (statique."coordonneesXY"::geometry) AS longitude,
    ST_Y (statique."coordonneesXY"::geometry) AS latitude,
    $level_id AS level_id
FROM
    lateststatus
    INNER JOIN statique ON lateststatus.id_pdc_itinerance = statique.id_pdc_itinerance
    $join_extras
WHERE
    $level_id IN ($indexes)
    AND horodatage >= timestamp $start

GROUP BY
    statique.id_pdc_itinerance,
    statique.id_station_itinerance,
    statique.puissance_nominale,
    longitude,
    latitude,
    $level_id
"""
QUERY_NATIONAL_TEMPLATE = """
SELECT
    statique.id_pdc_itinerance,
    statique.id_station_itinerance,
    statique.puissance_nominale,
    ST_X (statique."coordonneesXY"::geometry) AS longitude,
    ST_Y (statique."coordonneesXY"::geometry) AS latitude
FROM
    lateststatus
    INNER JOIN statique ON lateststatus.id_pdc_itinerance = statique.id_pdc_itinerance
WHERE
    horodatage >= timestamp $start
GROUP BY
    statique.id_pdc_itinerance,
    statique.id_station_itinerance,
    statique.puissance_nominale,
    longitude,
    latitude
"""


@task(task_run_name="values-for-target-{level:02d}", cache_policy=NONE)
def get_values_for_targets(
    level: Level,
    start: datetime,
    indexes: List[UUID],
    environment: Environment,
) -> pd.DataFrame:
    """Fetch points of charge given input level and target index."""
    query_template = Template(LIST_POCS_FOR_LEVEL_QUERY_TEMPLATE)
    query_params: dict = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}
    query_params |= get_num_for_level_query_params(level)
    query_params |= {"start": f"'{start.isoformat(sep=' ')}'"}
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )


@flow(
    flow_run_name="e5-{timespan.period.value}-{level:02d}-{timespan.start:%y-%m-%d}",
)
def e5_for_level(
    level: Level,
    timespan: IndicatorTimeSpan,
    environment: Environment,
    chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate e5 for a level."""
    start_lateststatus = timespan.start - PeriodDuration.MONTH.value
    if level == Level.NATIONAL:
        return e5_national(timespan, start_lateststatus, environment)
    targets = get_targets_for_level(level, environment)
    ids = targets["id"]
    chunks = (
        np.array_split(ids, int(len(ids) / chunk_size))
        if len(ids) > chunk_size
        else [ids.to_numpy()]
    )
    futures = [
        get_values_for_targets.submit(level, start_lateststatus, chunk, environment)  # type: ignore[call-overload]
        for chunk in chunks
    ]
    wait(futures)

    # Concatenate results and serialize indicators
    results = pd.concat([future.result() for future in futures], ignore_index=True)

    grp = results.groupby("level_id")
    results_list = pd.DataFrame()
    results_list["level_id"] = [name for name, group in grp]
    results_list["extras"] = [
        {
            "id_pdc_itinerance": list(group["id_pdc_itinerance"]),
            "id_station_itinerance": list(group["id_station_itinerance"]),
            "puissance_nominale": list(group["puissance_nominale"]),
            "latitude": list(group["latitude"]),
            "longitude": list(group["longitude"]),
        }
        for name, group in grp
    ]  # type: ignore[assignment]
    results_list["value"] = [
        len(list(group["id_pdc_itinerance"])) for name, group in grp
    ]

    merged = targets.merge(results_list, how="left", left_on="id", right_on="level_id")

    # Build result DataFrame
    indicators = {
        "target": merged["code"],
        "value": merged["value"].fillna(0),
        "code": "e5",
        "level": level,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": None,
        "extras": merged["extras"].fillna(
            pd.Series(
                [
                    {
                        "id_pdc_itinerance": [],
                        "id_station_itinerance": [],
                        "puissance_nominale": [],
                        "latitude": [],
                        "longitude": [],
                    }
                ]
                * len(merged)
            )
        ),
    }
    return pd.DataFrame(indicators)


@flow(
    flow_run_name="e5-{timespan.period.value}-00-{timespan.start:%y-%m-%d}",
)
def e5_national(
    timespan: IndicatorTimeSpan,
    start: datetime,
    environment: Environment,
) -> pd.DataFrame:
    """Calculate e5 at the national level."""
    query_template = Template(QUERY_NATIONAL_TEMPLATE)
    query_params = {"start": f"'{start.isoformat(sep=' ')}'"}
    with Session(get_api_db_engine(environment)) as session:
        result = pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )
    indicators = {
        "target": "00",
        "value": len(result),
        "code": "e5",
        "level": Level.NATIONAL,
        "period": timespan.period,
        "timestamp": timespan.start.isoformat(),
        "category": None,
        "extras": [
            {
                "id_pdc_itinerance": list(result["id_pdc_itinerance"]),
                "id_station_itinerance": list(result["id_station_itinerance"]),
                "puissance_nominale": list(result["puissance_nominale"]),
                "latitude": list(result["latitude"]),
                "longitude": list(result["longitude"]),
            }
        ],
    }
    return pd.DataFrame(indicators)


@flow(
    flow_run_name="meta-e5-{period.value}",
)
def e5(  # noqa: PLR0913
    environment: Environment,
    levels: List[Level],
    start: datetime | None = None,
    offset: int = -1,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    chunk_size: int = 1000,
    create_artifact: bool = False,
    persist: bool = False,
) -> pd.DataFrame:
    """Run all e5 subflows."""
    start = (
        datetime.now()
        if not offset and start is None
        else get_period_start_from_pit(start, offset, period)
    )
    timespan = IndicatorTimeSpan(period=period, start=start)
    subflows_results = [
        e5_for_level(level, timespan, environment, chunk_size=chunk_size)
        for level in levels
    ]
    indicators = pd.concat(subflows_results, ignore_index=True)
    description = f"e5 report at {timespan.start} (period: {timespan.period.value})"
    flow_name = runtime.flow_run.name
    export_indicators(
        indicators, environment, flow_name, description, create_artifact, persist
    )
    return indicators
