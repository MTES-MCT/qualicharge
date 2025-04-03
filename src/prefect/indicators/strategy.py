"""QualiCharge prefect indicators: strategy."""

# extract
from .extract.e4 import HISTORY_STRATEGY_FIELD as E4_STRATEGY

# infrastructure
from .infrastructure.i1 import HISTORY_STRATEGY_FIELD as I1_STRATEGY
from .infrastructure.t1 import HISTORY_STRATEGY_FIELD as T1_STRATEGY

STRATEGY = {"i1": I1_STRATEGY, "t1": T1_STRATEGY, "e4": E4_STRATEGY}
