"""QualiCharge prefect indicators: entrypoint."""

# ruff: noqa: F401
from .infrastructure.i1 import calculate as i1_calculate
from .infrastructure.i4 import calculate as i4_calculate
from .infrastructure.i7 import calculate as i7_calculate
from .infrastructure.t1 import calculate as t1_calculate
