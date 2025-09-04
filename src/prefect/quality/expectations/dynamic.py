"""Expectations for the dynamic data."""

from copy import copy
from datetime import date, timedelta
from string import Template

import great_expectations as gx
import great_expectations.expectations as gxe

from .parameters import ENEU

NAME: str = "dynamic"


def get_suite(date_start: date, date_end: date):
    """Get dynamic expectation suite."""
    date_params = {
        "start": f"'{date_start.isoformat()}'",
        "end": f"'{date_end.isoformat()}'",
    }
    energy_expectations = [
        # ENEU : Energy greater than max_energy (rule 11)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  session_f AS (
    SELECT
      *
    FROM
      SESSION
    WHERE
      energy > $max_energy_kwh
      AND START >= $start
      AND START < $end
  )
SELECT
  energy,
  nom_amenageur,
  START,
  SESSION_f.end,
  id_pdc_itinerance
FROM
  SESSION_f
  INNER JOIN ({batch}) AS statique_amenageur ON point_de_charge_id = pdc_id
                """
            ).substitute(
                date_params | ENEU.params  # type: ignore
            ),
            meta={"code": ENEU.code},
        )
    ]
    suite = gx.ExpectationSuite(name=NAME)
    expectations = energy_expectations
    for expectation in expectations:
        # Make sure expectation is not already assigned to a suite…
        exp = copy(expectation)
        exp.id = None
        # …before adding it to the current suite.
        suite.add_expectation(exp)
    return suite
