"""QualiCharge prefect quality tests: dynamic data."""

from datetime import date

from indicators.types import Environment
from quality.flows import dynamic, quality_run

NEW_NOW = date(year=2025, month=1, day=1)
FROM_NOW = {"days": 15}
DURATION = {"days": 7}


def test_run_api_db_validation():
    """Run API database validation."""
    results = dynamic.run_api_db_validation(
        Environment.TEST,
        DURATION,
        from_now=FROM_NOW,
        report_by_email=False,
        new_now=NEW_NOW,
    )
    for _, v in results.run_results.items():
        for result in v.results:
            code = result.expectation_config.meta.get("code")  # type: ignore[union-attr]
            if code in ["FRES", "FRET", "ENEX", "ENEA", "OCCT", "SEST"]:
                assert not result.success
            else:
                assert result.success


def test_run_api_db_validation_by_amenageur(monkeypatch):
    """Run API database validation by amenageur."""
    monkeypatch.setattr(
        quality_run,
        "get_db_amenageurs",
        lambda _: ["Tesla", "Ionity", "TesLa ", "Electra"],
    )
    report = dynamic.run_api_db_validation_by_amenageur(
        Environment.TEST,
        DURATION,
        from_now=FROM_NOW,
        report_by_email=False,
        new_now=NEW_NOW,
    )
    assert report.name == "dynamic-test"
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
                    if result.code in ["FRES", "FRET", "OCCT", "SEST"]:
                        assert not result.success
                    else:
                        assert result.success
                case "Ionity":
                    if result.code in ["FRES", "FRET", "ENEX", "ENEA", "OCCT", "SEST"]:
                        assert not result.success
                    else:
                        assert result.success
                case "Electra":
                    if result.code in ["FRES", "FRET", "ENEX", "ENEA", "OCCT", "SEST"]:
                        assert not result.success
                    else:
                        assert result.success
