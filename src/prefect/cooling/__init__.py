"""Prefect: cooling module."""

from datetime import date
from string import Template
from typing import List

from data7.models import Dataset
from data7.streamers import sql2parquet
from prefect import task
from prefect.client.schemas.objects import State
from prefect.states import Completed, Failed
from pyarrow import fs
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
    s3_endpoint_url: str,
    select_query: Template,
    check_query: Template,
    chunk_size: int = 5000,
) -> State:
    """Cool data from an environment on a particular day.

    This task creates a parquet file per-environment per-day and save it in a S3 bucket.
    """
    day_iso: str = day.isoformat()

    # Dataset
    basename = f"{bucket}-{day_iso}-{environment.value}"
    query = select_query.substitute({"date": day_iso})
    dataset = Dataset(basename=basename, query=query)

    # Target bucket
    s3 = fs.S3FileSystem(endpoint_override=s3_endpoint_url)
    dir_path = f"{bucket}/{day.year}/{day.month}/{day.day}"
    file_path = f"{dir_path}/{environment}.parquet"

    # Start writing dataset to the target bucket
    s3.create_dir(dir_path)
    with s3.open_output_stream(file_path) as archive:
        for chunk in sql2parquet(engine, dataset, chunksize=chunk_size):
            archive.write(chunk)

    # Check that the archive contains expected number of records
    with engine.connect() as connection:
        expected = connection.execute(
            text(check_query.substitute({"date": day_iso}))
        ).first()._tuple()[0]  # type: ignore[union-attr]
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
    s3_endpoint_url: str,
    days_to_extract_query: Template,
    select_query: Template,
    check_query: Template,
    chunk_size: int = 5000,
):
    """Extract data older than now - interval to daily archives."""
    db_engine = get_api_db_engine(environment)

    tasks_state : List[State]= []
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
            s3_endpoint_url,
            select_query,
            check_query,
            chunk_size=chunk_size,
        )
        tasks_state.append(state)
    return tasks_state
