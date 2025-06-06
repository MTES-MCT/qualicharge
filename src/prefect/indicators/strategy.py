"""QualiCharge prefect indicators: strategy."""

# extract
from .extract.e4 import HISTORY_STRATEGY_FIELD as E4_STRATEGY

# infrastructure
from .infrastructure.i1 import HISTORY_STRATEGY_FIELD as I1_STRATEGY
from .infrastructure.i4 import HISTORY_STRATEGY_FIELD as I4_STRATEGY
from .infrastructure.i7 import HISTORY_STRATEGY_FIELD as I7_STRATEGY
from .infrastructure.t1 import HISTORY_STRATEGY_FIELD as T1_STRATEGY

# usage
from .usage.u5 import HISTORY_STRATEGY_FIELD as U5_STRATEGY
from .usage.u6 import HISTORY_STRATEGY_FIELD as U6_STRATEGY
from .usage.u9 import HISTORY_STRATEGY_FIELD as U9_STRATEGY
from .usage.u10 import HISTORY_STRATEGY_FIELD as U10_STRATEGY
from .usage.u11 import HISTORY_STRATEGY_FIELD as U11_STRATEGY
from .usage.u12 import HISTORY_STRATEGY_FIELD as U12_STRATEGY
from .usage.u13 import HISTORY_STRATEGY_FIELD as U13_STRATEGY

STRATEGY = {
    "i1": I1_STRATEGY,
    "i4": I4_STRATEGY,
    "i7": I7_STRATEGY,
    "t1": T1_STRATEGY,
    "e4": E4_STRATEGY,
    "u5": U5_STRATEGY,
    "u6": U6_STRATEGY,
    "u9": U9_STRATEGY,
    "u10": U10_STRATEGY,
    "u11": U11_STRATEGY,
    "u12": U12_STRATEGY,
    "u13": U13_STRATEGY,
}
