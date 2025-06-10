"""Prefect: cooling module."""

from datetime import date
from enum import StrEnum
from string import Template
from typing import List, Tuple

from data7.models import Dataset
from data7.streamers import sql2parquet
from prefect import task
from prefect.client.schemas.objects import State
from prefect.logging import get_run_logger
from prefect.states import Completed, Failed
from pyarrow import fs
from pyarrow import parquet as pq
from sqlalchemy import Engine, text

from indicators.db import get_api_db_engine
from indicators.types import Environment


class IfExistStrategy(StrEnum):
    """Strategies to apply if archive already exists."""

    IGNORE = "ignore"
    CHECK = "check"
    FAIL = "fail"
    OVERWRITE = "overwrite"
    APPEND = "append"


def _check_archive(
    engine: Engine,
    day_iso: str,
    s3: fs.S3FileSystem,
    file_path: str,
    check_query: Template,
) -> Tuple[bool, int, int]:
    """Check generated archive size."""
    with engine.connect() as connection:
        result = connection.execute(
            text(check_query.substitute({"date": day_iso}))
        ).first()

        # No entry was found in database.
        # We do not check archive even if it exists, but in this case we return:
        # (False, 0, 0)
        if not result:
            return not s3.exists(file_path), 0, 0

        expected = result._tuple()[0]
    archive = pq.ParquetFile(file_path, filesystem=s3)
    n_rows = archive.scan_contents()
    archive.close()
    return n_rows == expected, n_rows, expected


@task
def extract_data_for_day(
    engine: Engine,
    day: date,
    environment: Environment,
    bucket: str,
    s3_endpoint_url: str,
    select_query: Template,
    check_query: Template,
    if_exists: IfExistStrategy = IfExistStrategy.FAIL,
    chunk_size: int = 5000,
) -> State:
    """Cool data from an environment on a particular day.

    This task creates a parquet file per-environment per-day and save it in a S3 bucket.
    """
    day_iso: str = day.isoformat()
    logger = get_run_logger()

    # Dataset
    basename = f"{bucket}-{day_iso}-{environment.value}"
    query = select_query.substitute({"date": day_iso})
    dataset = Dataset(basename=basename, query=query)

    # Target bucket
    s3 = fs.S3FileSystem(endpoint_override=s3_endpoint_url)
    dir_path = f"{bucket}/{day.year}/{day.month}/{day.day}"
    file_path = f"{dir_path}/{environment}.parquet"

    # Default output stream method
    s3_open_output_stream = s3.open_output_stream

    # Apply a strategy if the output file exists
    file_info = s3.get_file_info(file_path)
    if file_info.type in (fs.FileType.File, fs.FileType.Directory):
        match if_exists:
            case IfExistStrategy.IGNORE:
                return Completed(
                    message=(
                        f"{bucket} archive '{file_path}' already exists."
                        " Task will be considered as completed."
                    )
                )
            case IfExistStrategy.CHECK:
                ok, n_rows, expected = _check_archive(
                    engine, day_iso, s3, file_path, check_query
                )
                if not ok:
                    return Failed(
                        message=(
                            f"{bucket} archive '{file_path}' and database content"
                            f" have diverged ({n_rows} vs {expected} expected rows)"
                        )
                    )
                return Completed(
                    message=(
                        f"{bucket} archive '{file_path}' already exists and"
                        f" has been checked. It contains {n_rows} rows."
                    )
                )
            case IfExistStrategy.FAIL:
                return Failed(
                    message=(f"{bucket} archive '{file_path}' already exists!")
                )
            case IfExistStrategy.OVERWRITE:
                logger.warning(
                    f"{bucket} archive '{file_path}' already exists and "
                    "will be overwritten."
                )
            case IfExistStrategy.APPEND:
                s3_open_output_stream = s3.open_append_stream
                logger.warning(
                    f"{bucket} archive '{file_path}' already exists and "
                    "will be concatenated with hot data."
                )
                # FIXME
                return Failed(
                    message=(
                        f"{bucket} archive '{file_path}' already exists and "
                        "concatenation for S3 has not been implemented yet."
                    )
                )

    # Start writing dataset to the target bucket
    s3.create_dir(dir_path)
    with s3_open_output_stream(file_path) as archive:
        for chunk in sql2parquet(engine, dataset, chunksize=chunk_size):
            archive.write(chunk)

    # Check that the archive contains expected number of records
    ok, n_rows, expected = _check_archive(engine, day_iso, s3, file_path, check_query)
    if not ok:
        return Failed(
            message=(
                f"{bucket} archive '{file_path}' and database content"
                f" have diverged ({n_rows} vs {expected} expected rows)"
            )
        )

    return Completed(message=f"{bucket} archive '{file_path}' created")


def extract_data_older_than(
    older_than: date,
    environment: Environment,
    bucket: str,
    s3_endpoint_url: str,
    days_to_extract_query: Template,
    select_query: Template,
    check_query: Template,
    if_exists: IfExistStrategy = IfExistStrategy.FAIL,
    chunk_size: int = 5000,
):
    """Extract data older than a date to daily archives."""
    db_engine = get_api_db_engine(environment)

    tasks_state: List[State] = []
    with db_engine.connect() as connection:
        days = [
            row[0]
            for row in connection.execute(
                text(days_to_extract_query.substitute({"older_than": older_than}))
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
            if_exists=if_exists,
            chunk_size=chunk_size,
        )
        tasks_state.append(state)
    return tasks_state
