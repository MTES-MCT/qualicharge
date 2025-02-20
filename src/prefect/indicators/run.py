"""QualiCharge prefect indicators: entrypoint."""

# ruff: noqa: F401
from .infrastructure.i1 import calculate as i1_calculate
from .infrastructure.i4 import calculate as i4_calculate
from .infrastructure.i7 import calculate as i7_calculate
from .infrastructure.t1 import calculate as t1_calculate
from .usage.c1 import calculate as c1_calculate
from .usage.c2 import calculate as c2_calculate
from .usage.u5 import calculate as u5_calculate
from .usage.u6 import calculate as u6_calculate
from .usage.u9 import calculate as u9_calculate
from .usage.u10 import calculate as u10_calculate
from .usage.u11 import calculate as u11_calculate
from .usage.u12 import calculate as u12_calculate
from .usage.u13 import calculate as u13_calculate
