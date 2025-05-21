"""Prefect flows: cold statuses."""

from datetime import date
from string import Template

import s3fs
from data7.models import Dataset
from data7.streamers import sql2parquet
from prefect import flows, task

from indicators.db import get_api_db_engine
from indicators.types import Environment


STATUSES_FOR_A_DAY_QUERY_TEMPLATE = Template(
    """
    SELECT
        *
    FROM
        Status
    WHERE
        created_at::DATE = '$date'
    """
)


@task
def cold_statuses(
    day: date, environment: Environment, bucket: str, chunk_size: int = 5000
):
    """Cold statuses for an environment on a particular day."""
    day_iso: str = day.isoformat()

    # Dataset
    basename = f"statuses-{day_iso}-{environment.value}"
    query = STATUSES_FOR_A_DAY_QUERY_TEMPLATE.substitute({"date": day_iso})
    dataset = Dataset(basename=basename, query=query)

    # Source database engine
    db_engine = get_api_db_engine(environment)

    # Target bucket
    s3 = s3fs.S3FileSystem(anon=False)
    file_path = f"{bucket}/{day.year}/{day.month}/{day.day}/{environment}.parquet"

    # Start writing dataset to the target bucket
    with s3.open(file_path, "wb") as archive:
        for chunk in sql2parquet(db_engine, dataset, chunk_size=chunk_size):
            archive.write(chunk)

    # TODO:
    #   - check archive
    #   - return status


@task
def truncate_statuses(day: date, environment: Environment):
    """Truncate statuses for an environment on a particular day."""
