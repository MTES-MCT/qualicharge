"""Tests for the qcc.cli.auth module."""

from qcc.cli.auth import app


def test_cli_auth_whoami(runner, qcc, httpx_mock):
    """Test the `auth whoami` command."""
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/auth/whoami",
        json={"user": "johndoe"},
    )

    result = runner.invoke(app, obj=qcc)
    assert result.exit_code == 0
    assert result.stdout == "{'user': 'johndoe'}\n"
