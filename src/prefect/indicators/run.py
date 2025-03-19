"""QualiCharge prefect indicators: entrypoint."""

# ruff: noqa: F401

# extract
from .extract.e4 import calculate as e4_calculate

# historicize
from .historicize.up import calculate as up_calculate

# infrastructure
from .infrastructure.i1 import calculate as i1_calculate
from .infrastructure.i4 import calculate as i4_calculate
from .infrastructure.i7 import calculate as i7_calculate
from .infrastructure.t1 import calculate as t1_calculate

# usage
from .usage.u5 import calculate as u5_calculate
from .usage.u6 import calculate as u6_calculate
from .usage.u9 import calculate as u9_calculate
from .usage.u10 import calculate as u10_calculate
