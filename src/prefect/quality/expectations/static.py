"""Expectations for the `PointDeCharge` table."""

import great_expectations as gx
import great_expectations.expectations as gxe

NAME: str = "static"

pdc_expectations = [
    gxe.ExpectColumnMinToBeBetween(
        column="puissance_nominale",
        min_value=1.3,
    ),
    gxe.ExpectColumnMaxToBeBetween(
        column="puissance_nominale",
        max_value=4000,
    ),
]
amenageur_expectations = [
    gxe.ExpectColumnValuesToNotBeNull(column="nom_amenageur"),
    gxe.ExpectColumnValuesToNotBeNull(column="siren_amenageur"),
    gxe.ExpectColumnValuesToNotBeNull(column="contact_amenageur"),
]
operateur_expectations = [
    gxe.ExpectColumnValuesToNotBeNull(column="nom_operateur"),
    gxe.ExpectColumnValuesToNotBeNull(column="telephone_operateur"),
]


def set_expectation_suite(context):
    """Get `static` expectations suite."""
    if NAME in context.suites.all():
        return
    expectation_suite = context.suites.add(gx.ExpectationSuite(name=NAME))
    expectations = pdc_expectations
    expectations += amenageur_expectations
    expectations += operateur_expectations
    for expectation in expectations:
        expectation_suite.add_expectation(expectation)
