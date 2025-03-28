"""QualiCharge prefect indicators: entrypoint."""

# ruff: noqa: F401

# extract
from .extract.e4 import calculate as e4_calculate

# historicize
from .historicize.up import calculate as up_calculate

# infrastructure
from .infrastructure.i1 import calculate as i1_calculate
from .infrastructure.t1 import calculate as t1_calculate
