"""QualiCharge prefect cooling tests: statuses."""

import os

import pandas as pd
import pytest
from freezegun import freeze_time
from prefect.client.schemas.objects import StateType

import cooling
from cooling import IfExistStrategy
from cooling.statuses import extract_old_statuses
from indicators.types import Environment


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_extract_old_statuses_flow(clean_s3fs):
    """Test the `extract_old_statuses` flow."""
    with freeze_time("2025-07-01"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-statuses/2024/6/6/test.parquet"

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
    n_statuses = 2
    assert len(df) == n_statuses
    assert df["id_pdc_itinerance"][0] == "FRSE1ESE62MBBACP1"


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_extract_old_statuses_flow_check_fails(clean_s3fs, monkeypatch):
    """Test the `extract_old_statuses` flow when archive check fails."""

    # What if check fails?
    def fake_check(*args):
        return False, 1, 2

    monkeypatch.setattr(cooling, "_check_archive", fake_check)

    with freeze_time("2025-07-01"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-statuses/2024/6/6/test.parquet"

    assert len(result) == 1
    assert result[0].type == StateType.FAILED
    assert result[0].message == (
        f"qualicharge-statuses archive '{expected_path}' and database content"
        f" have diverged (1 vs 2 expected rows)"
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_extract_old_statuses_flow_archive_exists(clean_s3fs):
    """Test the `extract_old_statuses` flow when target archive exists."""
    with freeze_time("2025-07-01"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-statuses/2024/6/6/test.parquet"

    # We expect a single status older than a year
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert (
        result[0].message == f"qualicharge-statuses archive '{expected_path}' created"
    )

    # Test ignore strategy
    with freeze_time("2025-07-01"):
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
    with freeze_time("2025-07-01"):
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
    with freeze_time("2025-07-01"):
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
    with freeze_time("2025-07-01"):
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
def test_extract_old_statuses_flow_archive_exists_check(clean_s3fs, monkeypatch):
    """Test the `extract_old_statuses` flow when target archive exists."""
    with freeze_time("2025-07-01"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-statuses/2024/6/6/test.parquet"

    # We expect a single status older than a year
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert (
        result[0].message == f"qualicharge-statuses archive '{expected_path}' created"
    )

    with freeze_time("2025-07-01"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.CHECK,
        )
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert result[0].message == (
        f"qualicharge-statuses archive '{expected_path}' already exists "
        "and has been checked. It contains 2 rows."
    )

    # What happens when check fails?
    def fake_check(*args):
        return False, 1, 2

    monkeypatch.setattr(cooling, "_check_archive", fake_check)

    with freeze_time("2025-07-01"):
        result = extract_old_statuses(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.CHECK,
        )
    assert len(result) == 1
    assert result[0].type == StateType.FAILED
    assert result[0].message == (
        f"qualicharge-statuses archive '{expected_path}' and database content"
        f" have diverged (1 vs 2 expected rows)"
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_extract_old_statuses_flow_multiple_archives(clean_s3fs):
    """Test the `extract_old_statuses` flow when multiple archives are created."""
    with freeze_time("2024-07-16"):
        result = extract_old_statuses(
            from_now={"days": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_paths = [
        "qualicharge-statuses/2024/6/6/test.parquet",
        "qualicharge-statuses/2024/7/13/test.parquet",
        "qualicharge-statuses/2024/7/14/test.parquet",
    ]
    expected_statuses = [2, 3, 1]

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
