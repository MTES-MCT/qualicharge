"""Tests for the qcc.cli (main) module."""

from qcc.cli import app
from qcc.cli.codes import QCCExitCodes


def test_cli_main(runner):
    """Test the main `qcc` command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == QCCExitCodes.OK

    result = runner.invoke(
        app,
        [
            "--username",
            "foo",
            "--password",
            "bar",
            "--api-root-url",
            "http://fake/api/v1",
            "auth",
        ],
    )
    assert result.exit_code == QCCExitCodes.OK
