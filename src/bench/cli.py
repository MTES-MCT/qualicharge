#!/usr/bin/env python

"""Locust benchmark utility.

This client provides utilities to modify Locust output files.
"""

from pathlib import Path

import pandas as pd
import typer

import qualicharge

app = typer.Typer(no_args_is_help=True)


@app.command()
def stamp(csv_file: Path, revision: str):
    """Add date and version to locust stats csv file.

    It prints stamped CSV file in the standard output stream.
    """
    df = pd.read_csv(csv_file, dtype_backend="pyarrow")

    # Add metadata
    df["git"] = revision
    df["timestamp"] = pd.Timestamp.now(tz="utc")
    df["version"] = qualicharge.__version__
    typer.echo(df.to_csv(index=False))


@app.command()
def diff(database: Path, current: Path, short: bool = True):
    """Compare current bench with the last-known bench.

    Database path should point to the CSV file history, and current to the
    ran benchmark.
    """
    db = pd.read_csv(database, dtype_backend="pyarrow")
    bench = pd.read_csv(current, dtype_backend="pyarrow")

    # Get latest revision
    latest_revision = (
        db[["git", "timestamp"]].sort_values(by="timestamp").tail(1)["git"].iloc[0]
    )
    latest = db[db["git"] == latest_revision]
    latest.reset_index(drop=True, inplace=True)

    # Calculate diff
    cols = list(
        set(latest.columns.values) - {"Type", "Name", "git", "timestamp", "version"}
    )
    diff = bench[cols] - latest[cols]
    diff.insert(0, "Type", latest["Type"])
    diff.insert(1, "Name", latest["Name"])

    # Print result
    short_columns = [
        "Type",
        "Name",
        "Request Count",
        "Failure Count",
        "Median Response Time",
        "Average Response Time",
        "Min Response Time",
        "Max Response Time",
        "Average Content Size",
        "Requests/s",
    ]
    if short:
        typer.echo(diff[short_columns].to_csv(index=False))
    else:
        typer.echo(diff.to_csv(index=False))


if __name__ == "__main__":
    app()
