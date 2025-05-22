"""Prefect: cooling module."""

from datetime import date
from string import Template

import s3fs
from data7.models import Dataset
from data7.streamers import sql2parquet
from prefect import flow, task
from prefect.states import Completed, Failed
from pyarrow import parquet as pq
from sqlalchemy import Engine, text

from indicators.db import get_api_db_engine
from indicators.types import Environment


@task
def extract_data_for_day(
    engine: Engine,
    day: date,
    environment: Environment,
    bucket: str,
    select_query: Template,
    check_query: Template,
    chunk_size: int = 5000,
):
    """Cool data from an environment on a particular day.

    This task creates a parquet file per-environment per-day and save it in a S3 bucket.
    """
    day_iso: str = day.isoformat()

    # Dataset
    basename = f"{bucket}-{day_iso}-{environment.value}"
    query = select_query.substitute({"date": day_iso})
    dataset = Dataset(basename=basename, query=query)

    # Target bucket
    s3 = s3fs.S3FileSystem(anon=False)
    file_path = f"{bucket}/{day.year}/{day.month}/{day.day}/{environment}.parquet"

    # Start writing dataset to the target bucket
    with s3.open(file_path, "wb") as archive:
        for chunk in sql2parquet(engine, dataset, chunksize=chunk_size):
            archive.write(chunk)

    # Check that the archive contains expected number of records
    with engine.connect() as connection:
        expected = connection.execute(
            text(check_query.substitute({"date": day_iso}))
        ).first()[0]
    archive = pq.ParquetFile(file_path, filesystem=s3)
    n_rows = archive.scan_contents()
    archive.close()
    if n_rows != expected:
        return Failed(
            message=(
                f"{bucket} archive '{file_path}' is incomplete ({n_rows} vs {expected})"
            )
        )

    return Completed(message=f"{bucket} archive '{file_path}' created")


def extract_data_older_than(
    interval: str,
    environment: Environment,
    bucket: str,
    days_to_extract_query: Template,
    select_query: Template,
    check_query: Template,
    chunk_size: int = 5000,
):
    """Extract data older than now - interval to daily archives."""
    db_engine = get_api_db_engine(environment)

    tasks_state = []
    with db_engine.connect() as connection:
        days = [
            row[0]
            for row in connection.execute(
                text(days_to_extract_query.substitute({"interval": interval}))
            ).fetchall()
        ]
    for day in days:
        state = extract_data_for_day(
            db_engine,
            day,
            environment,
            bucket,
            select_query,
            check_query,
            chunk_size=chunk_size,
        )
        tasks_state.append(state)
    return tasks_state
