"""Expectations for the dynamic data."""

from copy import copy
from datetime import date, timedelta
from string import Template

import great_expectations as gx
import great_expectations.expectations as gxe

NAME: str = "dynamic"

# ENEU : Energy greater than 1000 kWh (rule 11)
ENEU_PARAMETER: dict = {"eneu_param": 1000}  # max energy (kWh) per session
ENEU_TEMPLATE: str = """
WITH
  session_f AS (
    SELECT
      *
    FROM
      SESSION
    WHERE
      energy > $eneu_param
      AND START >= $start_min
      AND START < $start_max
  )
SELECT
  energy,
  nom_amenageur,
  START,
  SESSION_f.end,
  puissance_nominale,
  id_pdc_itinerance,
  id_station_itinerance
FROM
  SESSION_f
  INNER JOIN {batch} ON point_de_charge_id = pdc_id
"""


def get_suite(from_now: dict):
    """Get dynamic expectation suite."""
    date_end = date.today()
    date_start = date_end - timedelta(**from_now)

    date_params = {
        "start_min": f"'{date_start.isoformat()}'",
        "start_max": f"'{date_end.isoformat()}'",
    }
    expectations = []

    # Energy greater than 500 kWh (rule 11)
    query_template = Template(ENEU_TEMPLATE)
    query_params = date_params | ENEU_PARAMETER
    expectations.append(
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=query_template.substitute(query_params),
            meta={"code": "ENEU"},
        )
    )

    suite = gx.ExpectationSuite(name=NAME)
    for expectation in expectations:
        # Make sure expectation is not already assigned to a suite…
        exp = copy(expectation)
        exp.id = None
        # …before adding it to the current suite.
        suite.add_expectation(exp)
    return suite
