"""QualiCharge prefect cooling tests: statuses."""

import os

import pandas as pd
import pytest
from freezegun import freeze_time
from prefect.client.schemas.objects import StateType

import cooling
from cooling import IfExistStrategy
from cooling.sessions import extract_old_sessions
from indicators.types import Environment


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_extract_old_sessions_flow(clean_s3fs):
    """Test the `extract_old_sessions` flow."""
    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-sessions/2022/10/24/test.parquet"

    # We expect a single status older than a year
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert (
        result[0].message == f"qualicharge-sessions archive '{expected_path}' created"
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
    assert df["id_pdc_itinerance"][0] == "FRS50E506600012"


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_extract_old_sessions_flow_check_fails(clean_s3fs, monkeypatch):
    """Test the `extract_old_sessions` flow when archive check fails."""

    # What if check fails?
    def fake_check(*args):
        return False, 1, 2

    monkeypatch.setattr(cooling, "_check_archive", fake_check)

    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-sessions/2022/10/24/test.parquet"

    assert len(result) == 1
    assert result[0].type == StateType.FAILED
    assert result[0].message == (
        f"qualicharge-sessions archive '{expected_path}' and database content"
        f" have diverged (1 vs 2 expected rows)"
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_extract_old_sessions_flow_archive_exists(clean_s3fs):
    """Test the `extract_old_sessions` flow when target archive exists."""
    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-sessions/2022/10/24/test.parquet"

    # We expect a single status older than a year
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert (
        result[0].message == f"qualicharge-sessions archive '{expected_path}' created"
    )

    # Test ignore strategy
    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert result[0].message == (
        f"qualicharge-sessions archive '{expected_path}' already exists. "
        "Task will be considered as completed."
    )

    # Test fail strategy
    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.FAIL,
        )
    assert len(result) == 1
    assert result[0].type == StateType.FAILED
    assert result[0].message == (
        f"qualicharge-sessions archive '{expected_path}' already exists!"
    )

    # Test overwrite strategy
    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.OVERWRITE,
        )
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert (
        result[0].message == f"qualicharge-sessions archive '{expected_path}' created"
    )

    # Test append strategy
    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.APPEND,
        )
    assert len(result) == 1
    assert result[0].type == StateType.FAILED
    assert result[0].message == (
        f"qualicharge-sessions archive '{expected_path}' already exists and "
        "concatenation for S3 has not been implemented yet."
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_extract_old_sessions_flow_archive_exists_check(clean_s3fs, monkeypatch):
    """Test the `extract_old_sessions` flow when target archive exists.

    Test the IfExistStrategy.CHECK scenario.
    """
    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_path = "qualicharge-sessions/2022/10/24/test.parquet"

    # We expect a single status older than a year
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert (
        result[0].message == f"qualicharge-sessions archive '{expected_path}' created"
    )

    # Test the CHECK strategy
    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.CHECK,
        )
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert result[0].message == (
        f"qualicharge-sessions archive '{expected_path}' already exists "
        "and has been checked. It contains 1 rows."
    )

    # What happens when check fails?
    def fake_check(*args):
        return False, 1, 2

    monkeypatch.setattr(cooling, "_check_archive", fake_check)

    with freeze_time("2025-05-15"):
        result = extract_old_sessions(
            from_now={"years": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.CHECK,
        )
    assert len(result) == 1
    assert result[0].type == StateType.FAILED
    assert result[0].message == (
        f"qualicharge-sessions archive '{expected_path}' and database content"
        f" have diverged (1 vs 2 expected rows)"
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_extract_old_sessions_flow_multiple_archives(clean_s3fs):
    """Test the `extract_old_sessions` flow when multiple archives are created."""
    with freeze_time("2024-12-03"):
        result = extract_old_sessions(
            from_now={"days": 1},
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )
    expected_paths = [
        "qualicharge-sessions/2022/10/24/test.parquet",
        "qualicharge-sessions/2024/11/30/test.parquet",
        "qualicharge-sessions/2024/12/1/test.parquet",
    ]
    expected_statuses = [1, 10, 1716]

    # We expect 3 archives
    assert len(result) == len(expected_paths)
    assert all(r.type == StateType.COMPLETED for r in result)
    assert all(
        r.message == f"qualicharge-sessions archive '{p}' created"
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
