"""Tiruert submission flows.

This is the core part that handles TIRUERT calculation for a quarter
and CARBURE API integration.
"""

from datetime import date

from prefect import flow, task

from indicators.types import Environment


@task
def aggregate(environment: Environment, from_date: date, to_date: date, code: str):
    """Aggregate daily calculation to a quarter for an operational unit."""


@task
def send():
    """Send volumes to carbure."""
