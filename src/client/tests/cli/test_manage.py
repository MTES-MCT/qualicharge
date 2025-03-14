"""Tests for the qcc.cli.status module."""

from qcc.cli.codes import QCCExitCodes
from qcc.cli.manage import app


def test_cli_manage_stations(runner, qcc, httpx_mock):
    """Test the `manage stations` command."""
    # No parameters
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/manage/station/siren/123456789",
        json=list(range(0, 10)),
    )
    result = runner.invoke(app, ["123456789"], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(10)) + "\n"

    # Filter: from_
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/manage/station/siren/123456789?after=2024-06-13T12%3A02%3A33",
        json=list(range(0, 2)),
    )
    result = runner.invoke(
        app, ["123456789", "--after", "2024-06-13T12:02:33"], obj=qcc
    )
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(2)) + "\n"

    # Raise an HTTP 500 error
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/manage/station/siren/123456789",
        status_code=500,
        json={"message": "An unknown error occured."},
    )
    result = runner.invoke(app, ["123456789"], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "An unknown error occured" in result.stdout

    # No station found
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/manage/station/siren/123456789",
        status_code=404,
        json={"message": "No station found."},
    )
    result = runner.invoke(app, ["123456789"], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "No station found." in result.stdout
