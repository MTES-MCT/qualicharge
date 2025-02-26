"""Expectations for the `PointDeCharge` table."""

import great_expectations as gx
import great_expectations.expectations as gxe


def get_expectation_suite(context, name="pdc"):
    """Get expectations suite for `PointDeCharge` table."""
    expectations = [
        gxe.ExpectColumnMinToBeBetween(
            column="puissance_nominale",
            min_value=1.3,
        ),
        gxe.ExpectColumnMaxToBeBetween(
            column="puissance_nominale",
            max_value=4000,
        ),
    ]
    expectation_suite = context.suites.add(gx.ExpectationSuite(name=name))
    for expectation in expectations:
        expectation_suite.add_expectation(expectation)
    return expectation_suite
