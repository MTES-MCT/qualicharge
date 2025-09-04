"""QualiCharge prefect quality tests: static data."""

import pytest

from indicators.types import Environment
from quality.flows import quality_run, static


def test_slugify():
    """Test the slugify utility from Django."""
    assert (
        quality_run.slugify("Comité interprofessionnel des vins de provence")
        == "comite-interprofessionnel-des-vins-de-provence"
    )


def test_get_db_amenageur():
    """Test the get_db_amenageur utility."""
    amenageurs = list(quality_run.get_db_amenageurs(Environment.TEST))
    expected = 25
    assert len(amenageurs) == expected

    with pytest.raises(
        LookupError, match="Undefined API database environment variable"
    ):
        next(quality_run.get_db_amenageurs(Environment.PRODUCTION))


def test_run_api_db_validation():
    """Run API database validation."""
    results = static.run_api_db_validation(Environment.TEST, report_by_email=False)
    for _, v in results.run_results.items():
        for result in v.results:
            code = result.expectation_config.meta.get("code")  # type: ignore[union-attr]
            if code in ["PDLM", "PDCL", "INSE"]:
                assert not result.success
            else:
                assert result.success


def test_run_api_db_validation_by_amenageur_with_unsafe_name(monkeypatch):
    """Run API database validation by amenageur with an unsafe name."""
    monkeypatch.setattr(
        quality_run,
        "get_db_amenageurs",
        lambda _: ["TERRITOIRE D'ENERGIE DU PUY-DE-DOME (TE 63)"],
    )
    report = static.run_api_db_validation_by_amenageur(
        Environment.TEST, report_by_email=False
    )
    for results in report.results:
        for result in results.suite:
            assert result.success


def test_run_api_db_validation_by_amenageur(monkeypatch):
    """Run API database validation by amenageur."""
    monkeypatch.setattr(
        quality_run,
        "get_db_amenageurs",
        lambda _: ["Tesla", "Ionity", "TesLa ", "Electra"],
    )
    report = static.run_api_db_validation_by_amenageur(
        Environment.TEST, report_by_email=False
    )
    assert report.name == "static-test"
    expected = 3
    assert len(report.results) == expected

    # (almost) all amenageurs should pass tests
    assert [r.amenageur for r in report.results] == ["Tesla", "Ionity", "Electra"]
    for results in report.results:
        successes = [s.success for s in results.suite]
        assert len(successes) == len(results.suite)

        for result in results.suite:
            match results.amenageur:
                case "Tesla":
                    if result.code == "PDLM":
                        assert not result.success
                    else:
                        assert result.success
                case "Ionity":
                    assert result.success
                case "Electra":
                    assert result.success
