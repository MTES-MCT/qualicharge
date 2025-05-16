"""QualiCharge prefect cooling tests: statuses."""

import os

import pandas as pd
import pytest
from freezegun import freeze_time
from prefect.client.schemas.objects import StateType

from cooling import IfExistStrategy
from cooling.statuses import extract_old_statuses
from indicators.types import Environment


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_extract_old_statuses_flow(clean_s3fs):
    """Test the `extract_old_statuses` flow."""
    with freeze_time("2025-05-15"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-statuses/2024/5/6/test.parquet"

    # We expect a single status older than a year
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert (
        result[0].message == f"qualicharge-statuses archive '{expected_path}' created"
    )

    # Assert parquet file exists and can be opened
    s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", None)
    df = pd.read_parquet(
        f"s3://{expected_path}",
        engine="pyarrow",
        dtype_backend="pyarrow",
        storage_options={
            "endpoint_url": s3_endpoint_url,
        },
    )
    # Check parquet file content
    assert len(df) == 1
    assert df["id_pdc_itinerance"][0] == "FRS63E63192AB1GT2"


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_extract_old_statuses_flow_archive_exists(clean_s3fs):
    """Test the `extract_old_statuses` flow."""
    with freeze_time("2025-05-15"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-statuses/2024/5/6/test.parquet"

    # We expect a single status older than a year
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert (
        result[0].message == f"qualicharge-statuses archive '{expected_path}' created"
    )

    # Test ignore strategy
    with freeze_time("2025-05-15"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert result[0].message == (
        f"qualicharge-statuses archive '{expected_path}' already exists. "
        "Task will be considered as completed."
    )

    # Test fail strategy
    with freeze_time("2025-05-15"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.FAIL,
        )
    assert len(result) == 1
    assert result[0].type == StateType.FAILED
    assert result[0].message == (
        f"qualicharge-statuses archive '{expected_path}' already exists!"
    )

    # Test overwrite strategy
    with freeze_time("2025-05-15"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.OVERWRITE,
        )
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert (
        result[0].message == f"qualicharge-statuses archive '{expected_path}' created"
    )

    # Test append strategy
    with freeze_time("2025-05-15"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.APPEND,
        )
    assert len(result) == 1
    assert result[0].type == StateType.FAILED
    assert result[0].message == (
        f"qualicharge-statuses archive '{expected_path}' already exists and "
        "concatenation for S3 has not been implemented yet."
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_extract_old_statuses_flow_multiple_archives(clean_s3fs):
    """Test the `extract_old_statuses` flow when multiple archives are created."""
    with freeze_time("2024-07-15"):
        result = extract_old_statuses(
            from_now={"days": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_paths = [
        "qualicharge-statuses/2024/5/6/test.parquet",
        "qualicharge-statuses/2024/7/9/test.parquet",
        "qualicharge-statuses/2024/7/13/test.parquet",
    ]
    expected_statuses = [1, 1, 2]

    # We expect 3 archives
    assert len(result) == len(expected_paths)
    assert all(r.type == StateType.COMPLETED for r in result)
    assert all(
        r.message == f"qualicharge-statuses archive '{p}' created"
        for r, p in zip(result, expected_paths, strict=True)
    )

    # Assert parquet files exist and can be opened
    s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", None)
    for expected_path, n in zip(expected_paths, expected_statuses, strict=True):
        df = pd.read_parquet(
            f"s3://{expected_path}",
            engine="pyarrow",
            dtype_backend="pyarrow",
            storage_options={
                "endpoint_url": s3_endpoint_url,
            },
        )
        # Check parquet file content
        assert len(df) == n
