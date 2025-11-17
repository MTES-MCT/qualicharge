"""QualiCharge prefect indicators: entrypoint."""

# ruff: noqa: F401

# extract
from .extract.e4 import calculate as e4_calculate

# historicize
from .historicize.up import calculate as up_calculate

# infrastructure
from .infrastructure.i1 import i1
from .infrastructure.i4 import i4
from .infrastructure.i7 import i7
from .infrastructure.t1 import t1

# usage
from .usage.u5 import calculate as u5_calculate
from .usage.u6 import calculate as u6_calculate
from .usage.u9 import calculate as u9_calculate
from .usage.u10 import calculate as u10_calculate
from .usage.u11 import calculate as u11_calculate
from .usage.u12 import calculate as u12_calculate
from .usage.u13 import calculate as u13_calculate
