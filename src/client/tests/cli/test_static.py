"""Tests for the qcc.cli.static module."""

import json

import pytest

from qcc.cli.codes import QCCExitCodes
from qcc.cli.static import app


def test_cli_static_list(runner, qcc, httpx_mock):
    """Test the `static list` command."""
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/",
        json={
            "items": list(range(0, 10)),
            "next": "http://example.com/api/v1/statique/?offset=10&limit=10",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/?offset=10&limit=10",
        json={"items": list(range(10, 20)), "next": None},
    )

    result = runner.invoke(app, ["list"], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert result.stdout == "\n".join(str(x) for x in range(20)) + "\n"

    # Raise an HTTP 500 error
    httpx_mock.add_response(
        method="GET",
        url="http://example.com/api/v1/statique/",
        status_code=500,
        json={"message": "An unknown error occured."},
    )

    result = runner.invoke(app, ["list"], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "An unknown error occured" in result.stdout


def test_cli_static_create(runner, qcc, httpx_mock):
    """Test the `static create` command."""
    # Empty interactive statique
    result = runner.invoke(app, ["create"], obj=qcc, input="\n")
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Invalid interactive input
    result = runner.invoke(app, ["create"], obj=qcc, input="foo\n")
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Missing --statique parameter in non-interactive mode
    result = runner.invoke(app, ["create", "--no-interactive"], obj=qcc)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert (
        "A statique object is required either from stdin or as an option"
        in result.stdout
    )

    statique = {"id_pdc_itinerance": "FRS63E0001"}
    statique_json = json.dumps(statique)
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/",
        json=statique,
    )

    # Valid parameter input
    result = runner.invoke(app, ["create", "--statique", statique_json], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert "Created statique successfully" in result.stdout

    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/",
        json=statique,
    )

    # Valid interactive input
    result = runner.invoke(app, ["create"], obj=qcc, input=f"{statique_json}\n")
    assert result.exit_code == QCCExitCodes.OK
    assert "Created statique successfully" in result.stdout

    # Raise an HTTP 500 error
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/",
        status_code=500,
        json={"message": "An unknown error occured."},
    )

    result = runner.invoke(app, ["create", "--statique", statique_json], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "An unknown error occured" in result.stdout


def test_cli_static_read(runner, qcc, httpx_mock):
    """Test the `static read` command."""
    id_pdc_itinerance = "FRS63E0001"
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}",
        json={"id_pdc_itinerance": id_pdc_itinerance},
    )

    result = runner.invoke(app, ["read", id_pdc_itinerance], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert '{"id_pdc_itinerance": "FRS63E0001"}' in result.stdout

    # Unknown PDC
    httpx_mock.add_response(
        method="GET",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}",
        status_code=404,
        json={"message": "PDC not found"},
    )
    result = runner.invoke(app, ["read", id_pdc_itinerance], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "PDC not found" in result.stdout


def test_cli_static_update(runner, qcc, httpx_mock):
    """Test the `static update` command."""
    # Empty interactive statique
    result = runner.invoke(app, ["update"], obj=qcc, input="\n")
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Invalid interactive input
    result = runner.invoke(app, ["update"], obj=qcc, input="foo\n")
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Missing --statique parameter in non-interactive mode
    result = runner.invoke(app, ["update", "--no-interactive"], obj=qcc)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert (
        "A statique object is required either from stdin or as an option"
        in result.stdout
    )

    # Statique entry is missing an id_pdc_itinerance field
    result = runner.invoke(app, ["update", "--statique", '{"foo": 1}'], obj=qcc)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Statique object requires an `id_pdc_itinerance` field" in result.stdout

    id_pdc_itinerance = "FRS63E0001"
    statique = {"id_pdc_itinerance": id_pdc_itinerance}
    statique_json = json.dumps(statique)
    httpx_mock.add_response(
        method="PUT",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}",
        json=statique,
    )

    # Valid parameter input
    result = runner.invoke(app, ["update", "--statique", statique_json], obj=qcc)
    assert result.exit_code == QCCExitCodes.OK
    assert "Updated statique successfully" in result.stdout

    httpx_mock.add_response(
        method="PUT",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}",
        json=statique,
    )

    # Valid interactive input
    result = runner.invoke(app, ["update"], obj=qcc, input=f"{statique_json}\n")
    assert result.exit_code == QCCExitCodes.OK
    assert "Updated statique successfully" in result.stdout

    # Raise an HTTP 500 error
    httpx_mock.add_response(
        method="PUT",
        url=f"http://example.com/api/v1/statique/{id_pdc_itinerance}",
        status_code=500,
        json={"message": "An unknown error occured."},
    )

    result = runner.invoke(app, ["update", "--statique", statique_json], obj=qcc)
    assert result.exit_code == QCCExitCodes.API_EXCEPTION
    assert "An error occurred while querying the API" in result.stdout
    assert "An unknown error occured" in result.stdout


@pytest.mark.parametrize("input", ("\n", "\n\n", " ", "foo", "{}\nfoo"))
def test_cli_static_bulk_invalid_input(runner, qcc, input):
    """Test the `static bulk` command with invalid inputs."""
    # Empty interactive statique
    result = runner.invoke(app, ["bulk"], obj=qcc, input=input)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout


def test_cli_static_bulk(runner, qcc, httpx_mock):
    """Test the `static bulk` command."""
    total = 12

    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/bulk",
        json={"size": 10},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/bulk",
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
    assert "Created 12 statiques successfully" in result.stdout

    # Insert invalid row in input
    input = "foo\n" + input
    result = runner.invoke(app, ["bulk"], obj=qcc, input=input)
    assert result.exit_code == QCCExitCodes.PARAMETER_EXCEPTION
    assert "Invalid JSON input string" in result.stdout

    # Badger mode: ignore all errors!
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/bulk",
        json={"size": 10},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://example.com/api/v1/statique/bulk",
        json={"size": 2},
    )
    result = runner.invoke(app, ["bulk", "--ignore-errors"], obj=qcc, input=input)
    assert result.exit_code == QCCExitCodes.OK
    assert "Created 12 statiques successfully" in result.stdout


@pytest.mark.parametrize("chunk_size", (5, 6, 10))
@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_cli_static_bulk_chunks(runner, qcc, httpx_mock, chunk_size):
    """Test the `static bulk` command with different chunk sizes."""
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
        url="http://example.com/api/v1/statique/bulk",
        json={"size": chunk_size},
    )
    result = runner.invoke(
        app, ["bulk", "--chunk-size", chunk_size], obj=qcc, input=input
    )
    assert result.exit_code == QCCExitCodes.OK
    assert "Created 30 statiques successfully" in result.stdout
