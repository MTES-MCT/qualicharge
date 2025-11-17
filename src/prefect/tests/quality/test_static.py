"""QualiCharge prefect quality tests: static data."""

import pytest
from sqlalchemy import text

from indicators.types import Environment
from quality.flows import quality_run, static


def test_get_db_units():
    """Test the get_db_units utility."""
    units = list(quality_run.get_db_units(Environment.TEST))
    expected = 20
    assert len(units) == expected

    with pytest.raises(
        LookupError, match="Undefined API database environment variable"
    ):
        next(quality_run.get_db_units(Environment.PRODUCTION))


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


def test_run_api_db_validation_by_unit_with_unsafe_name(monkeypatch):
    """Run API database validation by unit with an unsafe name."""
    monkeypatch.setattr(
        quality_run,
        "get_db_units",
        lambda _: ["FRS63"],
    )
    report = static.run_api_db_validation_by_unit(
        Environment.TEST, report_by_email=False
    )
    for results in report.results:
        for result in results.suite:
            assert result.success


def test_run_api_db_validation_by_unit(monkeypatch):
    """Run API database validation by unit."""
    monkeypatch.setattr(
        quality_run,
        "get_db_units",
        lambda _: ["FRTSL", "FRIOY", "FRELC"],
    )
    report = static.run_api_db_validation_by_unit(
        Environment.TEST, report_by_email=False
    )
    assert report.name == "static-test"
    expected = 3
    assert len(report.results) == expected

    # (almost) all units should pass tests
    assert [r.unit for r in report.results] == ["FRTSL", "FRIOY", "FRELC"]
    for results in report.results:
        successes = [s.success for s in results.suite]
        assert len(successes) == len(results.suite)

        for result in results.suite:
            match results.unit:
                case "FRTSL":
                    if result.code == "PDLM":
                        assert not result.success
                    else:
                        assert result.success
                case "FRIOY":
                    if result.code == "PDLM":
                        assert not result.success
                    else:
                        assert result.success
                case "FRELC":
                    if result.code == "PDLM":
                        assert not result.success
                    else:
                        assert result.success


def test_run_indicator_validation_by_unit(indicators_db_engine):
    """Run indicator validation by unit."""
    static.run_api_db_validation_by_unit(Environment.TEST, persist=True)
    with indicators_db_engine.connect() as connection:
        query = """
        select count(*) from test
        where target = 'FRTSL' and category = 'PDLM'
        """
        result = connection.execute(text(query))
        assert result.one()[0] == 1
