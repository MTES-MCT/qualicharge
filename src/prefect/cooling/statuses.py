"""Prefect flows: cooling statuses."""

from string import Template

from prefect import flow

from cooling import extract_data_older_than
from indicators.types import Environment


STATUSES_FOR_A_DAY_QUERY_TEMPLATE = Template(
    """
    SELECT
        PointDeCharge.id_pdc_itinerance,
        Status.*
    FROM
        Status
    INNER JOIN PointDeCharge ON Status.point_de_charge_id = PointDeCharge.id
    WHERE
        horodatage::DATE = '$date'
    """
)
STATUS_COUNT_FOR_A_DAY_QUERY_TEMPLATE = Template(
    """
    SELECT
        COUNT(*)
    FROM
        Status
    WHERE
        horodatage::DATE = '$date'
    """
)
STATUS_DAYS_TO_EXTRACT_QUERY_TEMPLATE = Template(
    """
    SELECT
      DISTINCT horodatage::DATE AS event_date
    FROM
      Status
    WHERE
      horodatage < NOW() - INTERVAL '$interval'
    GROUP BY
      event_date
    ORDER BY
      event_date
    """
)


@flow(log_prints=True)
def extract_old_statuses(
    interval: str, environment: Environment, chunk_size: int = 5000
):
    """Extract statuses older than now - interval to daily archives."""
    bucket = "qualicharge-statuses"
    return extract_data_older_than(
        interval,
        environment,
        bucket,
        STATUS_DAYS_TO_EXTRACT_QUERY_TEMPLATE,
        STATUSES_FOR_A_DAY_QUERY_TEMPLATE,
        STATUS_COUNT_FOR_A_DAY_QUERY_TEMPLATE,
        chunk_size=chunk_size,
    )
