"""Tests for the qcc.cli.status module."""

import json

import pytest

from qcc.cli.codes import QCCExitCodes
from qcc.cli.status import app


def test_cli_status_list(runner, qcc, httpx_mock):
    """Test the `status list` command."""
    # No parameters
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/",
        json=list(range(0, 10)),
    )
    result = runner.invoke(app, ["list"], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(10)) + "\n"

    # Filter: from_
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?from=2024-06-13T12%3A02%3A33",
        json=list(range(0, 2)),
    )
    result = runner.invoke(app, ["list", "--from", "2024-06-13T12:02:33"], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(2)) + "\n"

    # Filter: charge points
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?pdc=FR911E1111ER1",
        json=list(range(2, 5)),
    )
    result = runner.invoke(app, ["list", "--pdc", "FR911E1111ER1"], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(2, 5)) + "\n"

    # Filter: multiple charge points
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?pdc=FR911E1111ER1&pdc=FR911E1111ER2",
        json=list(range(1, 3)),
    )
    result = runner.invoke(
        app, ["list", "--pdc", "FR911E1111ER1", "--pdc", "FR911E1111ER2"], obj=qcc
    )
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(1, 3)) + "\n"

    # Filter: stations
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?station=FR911P0001",
        json=list(range(5, 10)),
    )
    result = runner.invoke(app, ["list", "--station", "FR911P0001"], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(5, 10)) + "\n"

    # Filter: stations + from_
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/?station=FR911P0001&from=2024-06-13T12%3A02%3A33",
        json=list(range(2, 8)),
    )
    result = runner.invoke(
        app,
        ["list", "--station", "FR911P0001", "--from", "2024-06-13T12:02:33"],
        obj=qcc,
    )
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(2, 8)) + "\n"

    # Raise an HTTP 500 error
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/status/",
        status_code=500,
        json={"message": "An unknown error occured."},
    )

    result = runner.invoke(app, ["list"], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "An unknown error occured" in result.stdout


def test_cli_status_read(runner, qcc, httpx_mock):
    """Test the `status read` command."""
    id_pdc_itinerance = "FRS63E0001"
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/dynamique/status/{id_pdc_itinerance}",
        json={"id_pdc_itinerance": id_pdc_itinerance},
    )

    result = runner.invoke(app, ["read", id_pdc_itinerance], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert '{"id_pdc_itinerance": "FRS63E0001"}' in result.stdout

    # Unknown PDC
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/dynamique/status/{id_pdc_itinerance}",
        status_code=404,
        json={"message": "PDC not found"},
    )
    result = runner.invoke(app, ["read", id_pdc_itinerance], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "PDC not found" in result.stdout


def test_cli_status_history(runner, qcc, httpx_mock):
    """Test the `status history` command."""
    id_pdc_itinerance = "FRS63E0001"
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/dynamique/status/{id_pdc_itinerance}/history",
        json=list(range(10)),
    )
    result = runner.invoke(app, ["history", id_pdc_itinerance], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(10)) + "\n"

    # Add --from option
    httpx_mock.add_response(
        method="GET",
        url=(
            f"http://example.com/api/v1/dynamique/status/{id_pdc_itinerance}"
            "/history?from=2024-06-13T12%3A02%3A33"
        ),
        json=list(range(3, 10)),
    )
    result = runner.invoke(
        app, ["history", id_pdc_itinerance, "--from", "2024-06-13T12:02:33"], obj=qcc
    )
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(3, 10)) + "\n"


def test_cli_status_create(runner, qcc, httpx_mock):
    """Test the `status create` command."""
    # Empty interactive status
    result = runner.invoke(app, ["create"], obj=qcc, input="\n")
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Invalid interactive input
    result = runner.invoke(app, ["create"], obj=qcc, input="foo\n")
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Missing --status parameter in non-interactive mode
    result = runner.invoke(app, ["create", "--no-interactive"], obj=qcc)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert (
        "A status object is required either from stdin or as an option" in result.stdout
    )

    status = {"id_pdc_itinerance": "FRS63E0001"}
    status_json = json.dumps(status)
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/",
        json=status,
    )

    # Valid parameter input
    result = runner.invoke(app, ["create", "--status", status_json], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert "Created status successfully" in result.stdout

    # Valid interactive input
    result = runner.invoke(app, ["create"], obj=qcc, input=f"{status_json}\n")
    assert result.exit_code == QCCExitCodes.OK
    assert "Created status successfully" in result.stdout

    # Raise an HTTP 500 error
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/",
        status_code=500,
        json={"message": "An unknown error occured."},
    )

    result = runner.invoke(app, ["create", "--status", status_json], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "An unknown error occured" in result.stdout


def test_cli_status_create_bulk(runner, qcc, httpx_mock):
    """Test the `status bulk` command."""
    total = 12

    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        json={"size": 10},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        json={"size": 2},
    )

    input = (
        "\n".join(
            [
                json.dumps({"id_pdc_itinerance": f"FRS63E00{x:02d}"})
                for x in range(total)
            ]
        )
        + "\n"
    )

    # Valid input
    result = runner.invoke(app, ["bulk"], obj=qcc, input=input)
    assert result.exit_code == QCCExitCodes.OK
    assert "Created 12 statuses successfully" in result.stdout

    # Insert invalid row in input
    input = "foo\n" + input
    result = runner.invoke(app, ["bulk"], obj=qcc, input=input)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Badger mode: ignore all errors!
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        json={"size": 10},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        json={"size": 2},
    )
    result = runner.invoke(app, ["bulk", "--ignore-errors"], obj=qcc, input=input)
    assert result.exit_code == QCCExitCodes.OK
    assert "Created 12 statuses successfully" in result.stdout


@pytest.mark.parametrize("chunk_size", (5, 6, 10))
def test_cli_status_bulk_chunks(runner, qcc, httpx_mock, chunk_size):
    """Test the `status bulk` command with different chunk sizes."""
    total = 30
    input = (
        "\n".join(
            [
                json.dumps({"id_pdc_itinerance": f"FRS63E00{x:02d}"})
                for x in range(total)
            ]
        )
        + "\n"
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/status/bulk",
        json={"size": chunk_size},
    )
    result = runner.invoke(
        app, ["bulk", "--chunk-size", chunk_size], obj=qcc, input=input
    )
    assert result.exit_code == QCCExitCodes.OK
    assert "Created 30 statuses successfully" in result.stdout
