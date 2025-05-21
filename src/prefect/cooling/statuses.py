"""Prefect flows: cooling statuses."""

from datetime import date
from string import Template

from numpy import select
from sqlalchemy import Connection

import s3fs
from data7.models import Dataset
from data7.streamers import sql2parquet
from prefect import flow, task
from prefect.states import Completed, Failed
from pyarrow import parquet as pq

from indicators.db import get_api_db_engine
from indicators.types import Environment

STATUSES_FOR_A_DAY_QUERY_TEMPLATE = Template(
    """
    SELECT
        *
    FROM
        Status
    WHERE
        horodatage::DATE = '$date'
    """
)
STATUS_COUNT_FOR_A_DAY_QUERY_TEMPLATE = Template(
    """
    SELECT
        COUNT(*)
    FROM
        Status
    WHERE
        horodatage::DATE = '$date'
    """
)
STATUS_DAYS_TO_EXTRACT_QUERY_TEMPLATE = Template(
    """
    SELECT
      DISTINCT horodatage::DATE AS event_date
    FROM
      Status
    WHERE
      horodatage < NOW() - INTERVAL '$interval'
    GROUP BY
      event_date
    ORDER BY
      event_date
    """
)


@task
def extract_data_for_day(
    connection: Connection,
    day: date,
    environment: Environment,
    bucket: str,
    select_query: Template,
    check_query: Template,
    chunk_size: int = 5000,
):
    """Cool data from an environment on a particular day."""
    day_iso: str = day.isoformat()

    # Dataset
    basename = f"statuses-{day_iso}-{environment.value}"
    query = select_query.substitute({"date": day_iso})
    dataset = Dataset(basename=basename, query=query)

    # Target bucket
    s3 = s3fs.S3FileSystem(anon=False)
    file_path = f"{bucket}/{day.year}/{day.month}/{day.day}/{environment}.parquet"

    # Start writing dataset to the target bucket
    with s3.open(file_path, "wb") as archive:
        for chunk in sql2parquet(connection, dataset, chunk_size=chunk_size):
            archive.write(chunk)

    # Check that the archive contains expected number of statuses
    expected = connection.execute(check_query.substitute({"date": day_iso})).first()
    archive = pq.ParquetFile(file_path)
    n_rows = archive.scan_contents()
    if n_rows != expected:
        return Failed(
            message=(
                f"Status archive '{file_path}' is incomplete ({n_rows} vs {expected})"
            )
        )

    return Completed(message=f"Status archive '{file_path}' created.")


@flow
def extract_old_statuses(
    interval: str, environment: Environment, chunk_size: int = 5000
):
    """Extract statuses older than now - interval to daily archives."""
    db_engine = get_api_db_engine(environment)

    bucket = "status"
    tasks_state = []
    with db_engine.connect() as connection:
        days = connection.execute(
            STATUS_DAYS_TO_EXTRACT_QUERY_TEMPLATE.substitute({"interval": interval})
        ).fetchall()
        for day in days:
            state = extract_data_for_day(
                connection,
                day,
                environment,
                bucket,
                STATUSES_FOR_A_DAY_QUERY_TEMPLATE,
                STATUS_COUNT_FOR_A_DAY_QUERY_TEMPLATE,
                chunk_size=chunk_size,
            )
            tasks_state.append(state)
    return tasks_state
