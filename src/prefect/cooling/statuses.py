"""Prefect flows: cooling statuses."""

import os
from datetime import date
from string import Template

from dateutil.relativedelta import relativedelta
from prefect import flow
from prefect.states import Failed

from cooling import IfExistStrategy, extract_data_older_than
from indicators.types import Environment

STATUSES_FOR_A_DAY_QUERY_TEMPLATE = Template("""
    SELECT
        PointDeCharge.id_pdc_itinerance,
        Status.*
    FROM
        Status
    INNER JOIN PointDeCharge ON Status.point_de_charge_id = PointDeCharge.id
    WHERE
        horodatage::DATE = '$date'
    """)
STATUS_COUNT_FOR_A_DAY_QUERY_TEMPLATE = Template("""
    SELECT
        COUNT(*)
    FROM
        Status
    WHERE
        horodatage::DATE = '$date'
    """)
STATUS_DAYS_TO_EXTRACT_QUERY_TEMPLATE = Template("""
    SELECT
      DISTINCT horodatage::DATE AS event_date
    FROM
      Status
    WHERE
      horodatage < '$older_than'
    GROUP BY
      event_date
    ORDER BY
      event_date
    """)


@flow(log_prints=True)
def extract_old_statuses(
    from_now: dict,
    environment: Environment,
    if_exists: IfExistStrategy = IfExistStrategy.FAIL,
    chunk_size: int = 5000,
):
    """Extract statuses older than now - from_now to daily archives."""
    s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", None)
    if s3_endpoint_url is None:
        return Failed(message="S3_ENDPOINT_URL environment variable not set.")
    bucket = "qualicharge-statuses"
    older_than = date.today() - relativedelta(**from_now)
    return extract_data_older_than(
        older_than,
        environment,
        bucket,
        s3_endpoint_url,
        STATUS_DAYS_TO_EXTRACT_QUERY_TEMPLATE,
        STATUSES_FOR_A_DAY_QUERY_TEMPLATE,
        STATUS_COUNT_FOR_A_DAY_QUERY_TEMPLATE,
        if_exists=if_exists,
        chunk_size=chunk_size,
    )
