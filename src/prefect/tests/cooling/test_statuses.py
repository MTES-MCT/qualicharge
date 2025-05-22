"""QualiCharge prefect cooling tests: statuses."""

import boto3
from moto import mock_aws

from cooling.statuses import extract_old_statuses


@mock_aws
def test_extract_old_statuses_flow():
    """Test the `extract_old_statuses` flow."""
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="qualicharge-statuses")

    result = extract_old_statuses(interval="1 year", environment="test")
    assert result == [True]
