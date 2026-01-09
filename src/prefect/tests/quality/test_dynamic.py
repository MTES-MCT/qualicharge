"""QualiCharge prefect quality tests: dynamic data."""

from datetime import date

from sqlalchemy import text

from indicators.models import IndicatorPeriod
from indicators.types import Environment
from quality.flows import dynamic, quality_run

NEW_NOW = date(year=2025, month=1, day=1)
FROM_NOW = {"days": 15}
PERIOD = {"days": 7}


def test_run_api_db_validation():
    """Run API database validation."""
    results = dynamic.run_api_db_validation(
        Environment.TEST,
        period=IndicatorPeriod.WEEK,
        from_now=FROM_NOW,
        report_by_email=False,
        new_now=NEW_NOW,
    )
    for _, v in results.run_results.items():
        for result in v.results:
            code = result.expectation_config.meta.get("code")  # type: ignore[union-attr]
            if code in ["FRES", "FRET", "ENEX", "ENEA", "OCCT", "SEST", "INAC"]:
                assert not result.success
            else:
                assert result.success


def test_run_api_db_validation_by_unit(monkeypatch):
    """Run API database validation by unit."""
    monkeypatch.setattr(
        quality_run,
        "get_db_units",
        lambda _: ["FRTSL", "FRIOY", "FRELC"],
    )
    report = dynamic.run_api_db_validation_by_unit(
        Environment.TEST,
        period=IndicatorPeriod.WEEK,
        from_now=FROM_NOW,
        report_by_email=False,
        new_now=NEW_NOW,
    )
    assert report.name == "dynamic-test"
    expected = 3
    assert len(report.results) == expected

    # (almost) all units should pass tests
    assert [r.unit for r in report.results] == ["FRTSL", "FRIOY", "FRELC"]
    for results in report.results:
        successes = [s.success for s in results.suite]
        assert len(successes) == len(results.suite)
        not_success_all = ["FRES", "FRET", "ENEA", "OCCT", "SEST", "INAC"]
        for result in results.suite:
            match results.unit:
                case "FRTSL":
                    if result.code in not_success_all:
                        assert not result.success
                    else:
                        assert result.success
                case "FRIOY":
                    if result.code in not_success_all + ["ENEX"]:
                        assert not result.success
                    else:
                        assert result.success
                case "FRELC":
                    if result.code in not_success_all + ["ENEX"]:
                        assert not result.success
                    else:
                        assert result.success


def test_run_indicator_validation_by_unit(indicators_db_engine):
    """Run indicator validation by unit."""
    dynamic.run_api_db_validation_by_unit(
        Environment.TEST,
        period=IndicatorPeriod.WEEK,
        from_now=FROM_NOW,
        report_by_email=False,
        new_now=NEW_NOW,
        persist=True,
    )
    with indicators_db_engine.connect() as connection:
        query = """
        select count(*) from test
        where target = 'FRIOY' and category = 'ENEX'
        """
        result = connection.execute(text(query))
        assert result.one()[0] == 1
