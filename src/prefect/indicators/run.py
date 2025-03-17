"""QualiCharge prefect indicators: entrypoint."""

# ruff: noqa: F401

# infrastructure
from .infrastructure.i1 import calculate as i1_calculate
from .infrastructure.t1 import calculate as t1_calculate
