"""Expectations for the dynamic data."""

from copy import copy
from string import Template

import great_expectations as gx
import great_expectations.expectations as gxe

NAME: str = "dynamic"

IS_DC: str = """(
puissance_nominale >= 50
OR prise_type_combo_ccs
OR prise_type_chademo
)"""

AFIREV_expectations = [
    # AFIREV format of stations not respected (rule 23)
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
SELECT
  id_station_itinerance
FROM
  {batch}
WHERE
  id_station_itinerance not like 'FR___P%'
        """,
        meta={"code": "DYNA"},
    ),
    # AFIREV format of charging points not respected (rule 24)
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
SELECT
  id_pdc_itinerance
FROM
  {batch}
WHERE
  id_pdc_itinerance not like 'FR___E%'
        """,
        meta={"code": "DYN2"},
    ),
]

def get_suite():
    """Get dynamic expectation suite."""
    suite = gx.ExpectationSuite(name=NAME)
    expectations = (
        AFIREV_expectations
    )
    for expectation in expectations:
        # Make sure expectation is not already assigned to a suite…
        exp = copy(expectation)
        exp.id = None
        # …before adding it to the current suite.
        suite.add_expectation(exp)
    return suite
