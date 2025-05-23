"""QualiCharge prefect cooling tests: statuses."""

from cooling.statuses import extract_old_statuses
from prefect.client.schemas.objects import StateType


def test_extract_old_statuses_flow():
    """Test the `extract_old_statuses` flow."""
    result = extract_old_statuses(interval="1 year", environment="test")

    # We expect a single status older than a year
    assert len(result) == 1
    assert result[0].type == StateType.COMPLETED
    assert result[0].message == (
        "qualicharge-statuses archive 'qualicharge-statuses/2024/5/6/test.parquet'"
        " created"
    )
