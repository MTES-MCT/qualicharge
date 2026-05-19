"""Tests for the qcc.cli.tariff module."""

import json

from qcc.cli.codes import QCCExitCodes
from qcc.cli.tariff import app


def test_cli_tariff_list(runner, qcc, httpx_mock):
    """Test the `tariff list` command."""
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/tariff/",
        json={"items": [{"id": "tariff-id"}]},
    )
    result = runner.invoke(app, ["list"], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert json.loads(result.stdout) == {"id": "tariff-id"}


def test_cli_tariff_create(runner, qcc, httpx_mock):
    """Test the `tariff create` command."""
    result = runner.invoke(app, ["create"], obj=qcc, input="\n")
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    result = runner.invoke(app, ["create", "--no-interactive"], obj=qcc)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert (
        "A tariff object is required either from stdin or as an option" in result.stdout
    )

    tariff = {"targets": [], "tariff": {"id": "t1", "elements": []}}
    tariff_json = json.dumps(tariff)
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/tariff/",
        json={"id": "tariff-id"},
    )
    result = runner.invoke(app, ["create", "--tariff", tariff_json], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert "Created tariff successfully" in result.stdout


def test_cli_tariff_read(runner, qcc, httpx_mock):
    """Test the `tariff read` command."""
    tariff_id = "4db7b976-faf4-4833-9728-a0bbf3bdf5fe"
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/statique/tariff/{tariff_id}",
        json={"id": tariff_id},
    )
    result = runner.invoke(app, ["read", tariff_id], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert json.loads(result.stdout) == {"id": tariff_id}


def test_cli_tariff_applicable(runner, qcc, httpx_mock):
    """Test the `tariff applicable` command."""
    id_pdc_itinerance = "FRS63E0001"
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}/tariff",
        json={"id": "tariff-id"},
    )
    result = runner.invoke(app, ["applicable", id_pdc_itinerance], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert json.loads(result.stdout) == {"id": "tariff-id"}


def test_cli_tariff_apply(runner, qcc, httpx_mock):
    """Test the `tariff apply` command."""
    id_pdc_itinerance = "FRS63E0001"
    tariff_id = "4db7b976-faf4-4833-9728-a0bbf3bdf5fe"
    httpx_mock.add_response(
        method="PUT",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}/tariff/{tariff_id}",
        json={"id": tariff_id},
    )
    result = runner.invoke(app, ["apply", id_pdc_itinerance, tariff_id], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert json.loads(result.stdout) == {"id": tariff_id}
