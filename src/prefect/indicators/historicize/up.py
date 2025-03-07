"""QualiCharge prefect indicators: historicization up."""

from datetime import datetime
from string import Template

import pandas as pd
from prefect import flow, runtime, task
from prefect.cache_policies import NONE
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy.orm import Session

from indicators.conf import settings
from indicators.db import get_indicators_db_engine
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, PeriodDuration
from indicators.strategy import STRATEGY
from indicators.types import Environment
from indicators.utils import export_indicators, get_period_start_from_pit

QUERY_HISTORICIZE = """
SELECT
    *
FROM
    $environment
WHERE
    period = '$period' AND
    timestamp >= '$start' AND
    timestamp < '$end'
"""
NULL_EXTRAS: dict = {"history": {}}
NULL_HISTORY: dict = {}

index_fields = ["code", "level", "target", "category"]
temporal_fields = ["period", "timestamp"]
value_fields = ["value"]
extras_fields = ["extras"]
# sum and sd are calculated : sum = mean * size, sd = sqrt(var)
summary_fields = ["size", "min", "max", "last", "var", "mean", "std", "sum"]
common_fields = index_fields + value_fields + summary_fields + temporal_fields


def decode_historicization_format(indicator: pd.DataFrame) -> pd.DataFrame:
    """Return a normalize DataFrame."""
    df_in = indicator.sort_values(by="timestamp").reset_index(drop=True)
    if "id" in df_in.columns:
        del df_in["id"]
    # groupby KO with NA values
    df_in["category"] = df_in["category"].fillna(" ")
    null_extras = pd.Series([NULL_EXTRAS] * len(df_in))
    if "extras" not in df_in.columns:
        df_in["extras"] = null_extras
    df_in["extras"] = df_in["extras"].fillna(null_extras)
    extras = pd.json_normalize(list(df_in["extras"]), max_level=0, errors="ignore")
    df_in = pd.concat([df_in, extras], axis=1)
    del df_in["extras"]

    null_history = pd.Series([NULL_HISTORY] * len(df_in))
    if "history" not in df_in.columns:
        df_in["history"] = null_history
    df_in["history"] = df_in["history"].fillna(null_history)
    history = pd.json_normalize(list(df_in["history"]), max_level=0, errors="ignore")
    df_in = pd.concat([df_in, history], axis=1)
    del df_in["history"]

    if "size" not in df_in.columns:
        df_in["size"] = 1
    df_in_value = df_in["value"].astype("float")
    if (df_in["size"] == 1).all():
        df_in["min"] = df_in_value
        df_in["max"] = df_in_value
        df_in["last"] = df_in_value
        df_in["mean"] = df_in_value
        df_in["sum"] = df_in_value
        df_in["var"] = 0.0
        df_in["std"] = 0.0
    return df_in


def calculate_historicization_up(
    df_in: pd.DataFrame, from_period: IndicatorPeriod
) -> pd.DataFrame:
    """Calculate an aggregation of data indicator."""
    # decode specific extras fields
    fld_extra_other = list(set(df_in.columns) - set(common_fields))
    extra_sum = [col for col in fld_extra_other if col[:4] == "sum_"]
    extra_min = [col for col in fld_extra_other if col[:4] == "min_"]
    extra_max = [col for col in fld_extra_other if col[:4] == "max_"]
    extra_mean = [col for col in fld_extra_other if col[:5] == "mean_"]
    extra_last = list(
        set(fld_extra_other) - set(extra_sum + extra_min + extra_max + extra_mean)
    )

    # add temporary fields to calculate mean values
    for col in extra_mean + ["mean"]:
        df_in[col + "_size"] = df_in[col] * df_in["size"]

    # add temporary fields to calculate the variance
    df_in["size_var"] = df_in["size"] * df_in["var"]
    df_in["size_mean"] = df_in["size"] * df_in["mean"]
    df_in["size_mean_square"] = df_in["size"] * df_in["mean"] ** 2

    # calculate DataFrame with new period
    grp = df_in.groupby(index_fields, sort=False)
    col_mean = [col + "_size" for col in extra_mean + ["mean"]]
    grp_sum = grp[
        col_mean + extra_sum + ["size", "size_var", "size_mean", "size_mean_square"]
    ].sum()
    df_up = grp_sum[["size"]].copy()
    for col in extra_mean + ["mean"]:
        df_up[col] = grp_sum[col + "_size"] / df_up["size"]
    for col in extra_sum:
        df_up[col] = grp_sum[col]
    grp_max = grp[extra_max + ["max"]].max()
    for col in extra_max + ["max"]:
        df_up[col] = grp_max[col]
    grp_min = grp[extra_min + ["min"]].min()
    for col in extra_min + ["min"]:
        df_up[col] = grp_min[col]
    grp_last = grp[extra_last + ["last"]].last()
    for col in extra_last + ["last"]:
        df_up[col] = grp_last[col]
    df_up["var"] = (
        grp_sum["size_var"] / df_up["size"]
        + df_up["mean"] ** 2
        - grp_sum["size_mean"] * 2 * df_up["mean"] / df_up["size"]
        + grp_sum["size_mean_square"] / df_up["size"]
    )
    df_up["std"] = df_up["var"].pow(0.5)
    df_up["sum"] = df_up["mean"] * df_up["size"]
    df_up["from"] = from_period.value
    return df_up.reset_index()


def encode_historicization_format(
    df_up: pd.DataFrame, timespan_up: IndicatorTimeSpan
) -> pd.DataFrame:
    """Return a nested DataFrame."""
    fld_extra_other = list(set(df_up.columns) - set(common_fields))
    df_up["history"] = df_up[summary_fields].to_dict(orient="records")
    df_up["extras"] = df_up[["history"] + fld_extra_other].to_dict(orient="records")
    df_up["timestamp"] = timespan_up.start.isoformat()
    df_up["period"] = timespan_up.period
    values = []
    for _idx, row in df_up.iterrows():
        values.append(row[STRATEGY[row["code"]]])
    df_up["value"] = pd.Series(values)
    return df_up[index_fields + value_fields + extras_fields + temporal_fields]


@task(
    task_run_name="to_historicization_up-{timespan_up.period.value}-{timespan_up.start:%y-%m-%d}",
    cache_policy=NONE,
)
def to_historicization_up(
    indicator: pd.DataFrame,
    from_period: IndicatorPeriod,
    timespan_up: IndicatorTimeSpan,
) -> pd.DataFrame:
    """Return an historicization for a new period."""
    flat_histo_df = decode_historicization_format(indicator)
    histo_up_df = calculate_historicization_up(flat_histo_df, from_period)
    return encode_historicization_format(histo_up_df, timespan_up)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-up-{to_period.value}-{start:%y-%m-%d}",
)
def calculate(  # noqa: PLR0913
    environment: Environment,
    to_period: IndicatorPeriod,
    start: datetime | None = None,
    offset: int = -1,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    create_artifact: bool = False,
    persist: bool = False,
) -> pd.DataFrame:
    """Add an historicization with a new period."""
    init_period = (
        datetime.now()
        if not offset and start is None
        else get_period_start_from_pit(start, offset, period)
    )
    final_timespan = IndicatorTimeSpan(start=init_period, period=to_period)
    query_params = {
        "environment": environment,
        "period": period.value,
        "start": init_period,
        "end": init_period + PeriodDuration[to_period.name].value,
    }
    query_template = Template(QUERY_HISTORICIZE)
    with Session(get_indicators_db_engine()) as session:
        histo_df = pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )
    histo_indicator = to_historicization_up(histo_df, period, final_timespan)
    description = (
        f"up report at {final_timespan.start} (period: {final_timespan.period.value})"
    )
    flow_name = runtime.flow_run.name
    export_indicators(
        histo_indicator, environment, flow_name, description, create_artifact, persist
    )
    return histo_indicator
