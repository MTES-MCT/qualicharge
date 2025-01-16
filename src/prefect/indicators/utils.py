"""QualiCharge prefect indicators: utils.

Common indicators functions and constants.
"""

from string import Template

import pandas as pd  # type: ignore
from prefect import task
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

from .conf import settings
from .models import IndicatorTimeSpan, Level, PeriodDuration

POWER_RANGE_CTE = """
    puissance(category, p_cat) AS (
        VALUES
            (numrange(0.0, 7.4), 1),
            (numrange(7.4, 22.0), 2),
            (numrange(22.0, 50.0), 3),
            (numrange(50, 150.0), 4),
            (numrange(150, 350.0), 5),
            (numrange(350, NULL), 6)
    )"""


def get_timespan_filter_query_params(timespan: IndicatorTimeSpan):
    """Get timespan query parameters."""
    date_end = timespan.start + PeriodDuration[timespan.period.name].value
    sql_start = "'" + timespan.start.isoformat(sep=" ") + "'"
    sql_end = "'" + date_end.isoformat(sep=" ") + "'"
    interval = "START >= timestamp $start AND START < timestamp $end"
    query_params = {"start": sql_start, "end": sql_end}
    return {"timespan": Template(interval).substitute(query_params)}


def get_num_for_level_query_params(level: Level):
    """Get level_id and join_extras query parameters."""
    match level:
        case Level.CITY:
            return {"level_id": "City.id", "join_extras": ""}
        case Level.EPCI:
            return {
                "level_id": "EPCI.id",
                "join_extras": "INNER JOIN EPCI ON City.epci_id = EPCI.id",
            }
        case Level.DEPARTMENT:
            return {
                "level_id": "Department.id",
                "join_extras": """
                    INNER JOIN Department ON City.department_id = Department.id
                    """,
            }
        case Level.REGION:
            return {
                "level_id": "Region.id",
                "join_extras": """
                    INNER JOIN Department ON City.department_id = Department.id
                    INNER JOIN Region ON Department.region_id = Region.id
                    """,
            }
        case _:
            raise NotImplementedError("Unsupported level %d", level)


@task
def get_database_engine() -> Engine:
    """Get QualiCharge API database engine."""
    return create_engine(str(settings.DATABASE_URL))


@task(task_run_name="targets-for-level-{level:02d}")
def get_targets_for_level(connection: Connection, level: Level) -> pd.DataFrame:
    """Get registered targets for level from QualiCharge database."""
    if level == Level.NATIONAL:
        raise NotImplementedError("Unsupported level %d", level)
    return pd.read_sql_table(level.name.lower(), con=connection)
