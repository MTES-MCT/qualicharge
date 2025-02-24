"""Expectations for the `PointDeCharge` table."""

from copy import copy

import great_expectations as gx
import great_expectations.expectations as gxe

NAME: str = "static"

pdc_expectations = [
    gxe.ExpectColumnMinToBeBetween(
        column="puissance_nominale",
        min_value=1.3,
        meta={"code": "POWL"},
    ),
    gxe.ExpectColumnMaxToBeBetween(
        column="puissance_nominale",
        max_value=4000,
        meta={"code": "POWU"},
    ),
]
amenageur_expectations = [
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_amenageur",
        meta={"code": "AMEM1"},
    ),
    gxe.ExpectColumnValuesToNotBeNull(
        column="siren_amenageur",
        meta={"code": "AMEM2"},
    ),
    gxe.ExpectColumnValuesToNotBeNull(
        column="contact_amenageur",
        meta={"code": "AMEM3"},
    ),
]
operateur_expectations = [
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_operateur",
        meta={"code": "OPEM1"},
    ),
    gxe.ExpectColumnValuesToNotBeNull(
        column="telephone_operateur",
        meta={"code": "OPEM2"},
    ),
]
localisation_expectations = [
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
SELECT
  id_station_itinerance,
  ST_X ("coordonneesXY"::geometry) AS longitude,
  ST_Y ("coordonneesXY"::geometry) AS latitude
FROM
  {batch}
WHERE
  (
    (
      ST_X ("coordonneesXY"::geometry) > 10
      OR ST_X ("coordonneesXY"::geometry) < -5
    )
    OR (
      ST_Y ("coordonneesXY"::geometry) > 52
      OR ST_Y ("coordonneesXY"::geometry) < 41
    )
  )
    """,
        meta={"code": "CRDS"},
    )
]


def get_suite():
    """Get static expectation suite."""
    suite = gx.ExpectationSuite(name="static")
    expectations = (
        pdc_expectations
        + amenageur_expectations
        + operateur_expectations
        + localisation_expectations
    )
    for expectation in expectations:
        # Make sure expectation is not already assigned to a suite…
        exp = copy(expectation)
        exp.id = None
        # …before adding it to the current suite.
        suite.add_expectation(exp)
    return suite
