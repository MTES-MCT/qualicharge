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
    expected = 25
    assert len(amenageurs) == expected

    with pytest.raises(
        LookupError, match="Undefined API database environment variable"
    ):
        next(static.get_db_amenageurs(Environment.PRODUCTION))


def test_run_api_db_validation():
    """Run API database validation."""
    result = static.run_api_db_validation(Environment.TEST, report_by_email=False)
    assert result.success


def test_run_api_db_validation_by_amenageur(monkeypatch):
    """Run API database validation by amenageur."""
    monkeypatch.setattr(
        static, "get_db_amenageurs", lambda _: ["Tesla", "Ionity", "TesLa ", "Electra"]
    )
    report = static.run_api_db_validation_by_amenageur(
        Environment.TEST, report_by_email=False
    )
    assert report.name == "static-test"
    expected = 3
    assert len(report.results) == expected

    # All amenageurs should pass tests
    assert [r.amenageur for r in report.results] == ["Tesla", "Ionity", "Electra"]
    for results in report.results:
        assert results.success
        successes = [s.success for s in results.suite]
        assert len(successes) == len(results.suite)
