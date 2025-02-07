"""Tests for the qcc.cli.session module."""

import json

import pytest

from qcc.cli.codes import QCCExitCodes
from qcc.cli.session import app


def test_cli_session_create(runner, qcc, httpx_mock):
    """Test the `session create` command."""
    # Empty interactive status
    result = runner.invoke(app, ["create"], obj=qcc, input="\n")
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Invalid interactive input
    result = runner.invoke(app, ["create"], obj=qcc, input="foo\n")
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Missing --session parameter in non-interactive mode
    result = runner.invoke(app, ["create", "--no-interactive"], obj=qcc)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert (
        "A session object is required either from stdin or as an option"
        in result.stdout
    )

    session = {"id_pdc_itinerance": "FRS63E0001"}
    status_json = json.dumps(session)
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/",
        json=session,
    )

    # Valid parameter input
    result = runner.invoke(app, ["create", "--session", status_json], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert "Created session successfully" in result.stdout

    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/",
        json=session,
    )

    # Valid interactive input
    result = runner.invoke(app, ["create"], obj=qcc, input=f"{status_json}\n")
    assert result.exit_code == QCCExitCodes.OK
    assert "Created session successfully" in result.stdout

    # Raise an HTTP 500 error
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/",
        status_code=500,
        json={"message": "An unknown error occured."},
    )

    result = runner.invoke(app, ["create", "--session", status_json], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "An unknown error occured" in result.stdout


def test_cli_session_create_bulk(runner, qcc, httpx_mock):
    """Test the `session bulk` command."""
    total = 12

    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/bulk",
        json={"size": 10},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/bulk",
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
    assert "Created 12 sessions successfully" in result.stdout

    # Insert invalid row in input
    input = "foo\n" + input
    result = runner.invoke(app, ["bulk"], obj=qcc, input=input)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Badger mode: ignore all errors!
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/bulk",
        json={"size": 10},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/dynamique/session/bulk",
        json={"size": 2},
    )
    result = runner.invoke(app, ["bulk", "--ignore-errors"], obj=qcc, input=input)
    assert result.exit_code == QCCExitCodes.OK
    assert "Created 12 sessions successfully" in result.stdout


@pytest.mark.parametrize("chunk_size", (5, 6, 10))
@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_cli_session_bulk_chunks(runner, qcc, httpx_mock, chunk_size):
    """Test the `session bulk` command with different chunk sizes."""
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
        url="http://example.com/api/v1/dynamique/session/bulk",
        json={"size": chunk_size},
    )
    result = runner.invoke(
        app, ["bulk", "--chunk-size", chunk_size], obj=qcc, input=input
    )
    assert result.exit_code == QCCExitCodes.OK
    assert "Created 30 sessions successfully" in result.stdout


def test_cli_session_check(runner, qcc, httpx_mock):
    """Test the `session bulk` command with different chunk sizes."""
    # The session exists
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/session/check?session_id=feab81dc-4ff9-4aca-8e1b-f364aec2eae5",
    )
    result = runner.invoke(
        app, ["check", "feab81dc-4ff9-4aca-8e1b-f364aec2eae5"], obj=qcc
    )
    assert result.exit_code == QCCExitCodes.OK
    assert "Session feab81dc-4ff9-4aca-8e1b-f364aec2eae5 exists." in result.stdout

    # The session does not exist
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/dynamique/session/check?session_id=feab81dc-4ff9-4aca-8e1b-f364aec4eae5",
        status_code=404,
    )
    result = runner.invoke(
        app, ["check", "feab81dc-4ff9-4aca-8e1b-f364aec4eae5"], obj=qcc
    )
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "Session not found." in result.stdout
