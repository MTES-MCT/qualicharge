"""Expectations for the `PointDeCharge` table."""

import great_expectations as gx
import great_expectations.expectations as gxe

NAME: str = "static"

pdc_expectations = [
    gxe.ExpectColumnMinToBeBetween(
        column="puissance_nominale",
        min_value=1.3,
        max_value=4000,
        meta={"code": "E001"},
    ),
    # gxe.ExpectColumnMaxToBeBetween(
    #     column="puissance_nominale",
    #     max_value=4000,
    # ),
]
amenageur_expectations = [
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_amenageur",
        meta={"code": "E002"},
    ),
    gxe.ExpectColumnValuesToNotBeNull(
        column="siren_amenageur",
        meta={"code": "E003"},
    ),
    gxe.ExpectColumnValuesToNotBeNull(
        column="contact_amenageur",
        meta={"code": "E004"},
    ),
]
operateur_expectations = [
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_operateur",
        meta={"code": "E005"},
    ),
    gxe.ExpectColumnValuesToNotBeNull(
        column="telephone_operateur",
        meta={"code": "E006"},
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
        meta={"code": "E007"},
    )
]


def set_expectation_suite(context):
    """Get `static` expectations suite."""
    if NAME in context.suites.all():
        return
    expectation_suite = context.suites.add(gx.ExpectationSuite(name=NAME))
    expectations = pdc_expectations
    expectations += amenageur_expectations
    expectations += operateur_expectations
    expectations += localisation_expectations
    for expectation in expectations:
        expectation_suite.add_expectation(expectation)
