"""QualiCharge prefect quality tests: static data."""

import pytest

from indicators.types import Environment
from quality.flows import static


def test_slugify():
    """Test the slugify utility from Django."""
    assert (
        static.slugify("Comité interprofessionnel des vins de provence")
        == "comite-interprofessionnel-des-vins-de-provence"
    )


def test_get_db_amenageur():
    """Test the get_db_amenageur utility."""
    amenageurs = list(static.get_db_amenageurs(Environment.TEST))
    expected = 507
    assert len(amenageurs) == expected

    with pytest.raises(
        LookupError, match="Undefined API database environment variable"
    ):
        next(static.get_db_amenageurs(Environment.PRODUCTION))


def test_run_api_db_validation():
    """Run API database validation."""
    result = static.run_api_db_validation(Environment.TEST, report_by_email=False)
    assert not result.success


def test_run_api_db_validation_by_amenageur(monkeypatch):
    """Run API database validation by amenageur."""
    monkeypatch.setattr(
        static, "get_db_amenageurs", lambda _: ["Tesla", "UAB", "TesLa ", "UNIBAIL"]
    )
    report = static.run_api_db_validation_by_amenageur(
        Environment.TEST, report_by_email=False
    )
    assert report.name == "static-test"
    expected = 3
    assert len(report.results) == expected

    # Tesla
    results = report.results[0]
    assert results.amenageur == "Tesla"
    assert not results.success
    successes = [s.success for s in report.results[0].suite]
    expectations = 8
    assert len(successes) == expectations
    exp_successes = 7
    assert len([s for s in successes if s]) == exp_successes

    # UAB
    results = report.results[1]
    assert results.amenageur == "UAB"
    assert not results.success
    successes = [s.success for s in report.results[1].suite]
    expectations = 8
    assert len(successes) == expectations
    exp_successes = 5
    assert len([s for s in successes if s]) == exp_successes

    # Unibail
    results = report.results[2]
    assert results.amenageur == "UNIBAIL"
    assert results.success
    successes = [s.success for s in report.results[2].suite]
    expectations = 8
    assert len(successes) == expectations
    exp_successes = 8
    assert len([s for s in successes if s]) == exp_successes
