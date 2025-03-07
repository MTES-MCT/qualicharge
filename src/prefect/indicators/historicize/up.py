"""QualiCharge prefect indicators: historicization up."""

from datetime import date, datetime
from string import Template

import pandas as pd
from dateutil.relativedelta import relativedelta
from prefect import flow, runtime, task
from prefect.cache_policies import NONE
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy.orm import Session

from indicators.conf import settings
from indicators.db import get_indicators_db_engine
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, PeriodDuration
from indicators.types import Environment
from indicators.utils import export_indicators

QUERY_HISTORICIZE = """
SELECT
    *
FROM
    development
WHERE
    period = '$period' AND
    timestamp >= '$start'   AND
    timestamp < '$end'
"""


@task(
    task_run_name="to_df_histo_up-{timespan_up.period.value}-{timespan_up.start:%y-%m-%d}",
    cache_policy=NONE,
)
def to_df_histo_up(
    indicator: pd.DataFrame, timespan_up: IndicatorTimeSpan
) -> pd.DataFrame:
    """Return an historicization for a new period."""
    # categorize the fields of the indicator DataFrame
    fld_index = ["code", "level", "target", "category"]
    fld_histo = ["period", "timestamp"]
    fld_value = ["value"]
    fld_extras = ["extras"]
    fld_extra_fixed = ["quantity", "mini", "maxi", "last", "variance"]

    # normalize the indicator DataFrame (add extras fields)
    df_in = indicator.sort_values(by="timestamp").reset_index(drop=True)
    df_in["category"] = df_in["category"].fillna(" ")  # groupby KO with NA values
    df_in["value"] = df_in["value"].astype("float")
    if "extras" in df_in.columns:
        df_in = pd.concat(
            [df_in, pd.json_normalize(df_in["extras"], errors="ignore")], axis=1
        )
        del df_in["extras"]
    if "quantity" not in df_in.columns:
        df_in["quantity"] = 1
    if (df_in["quantity"] == 1).all():
        df_in["mini"] = df_in["value"]
        df_in["maxi"] = df_in["value"]
        df_in["last"] = df_in["value"]
        df_in["variance"] = 0.0

    # decode specific extras fields
    fld_extra_other = list(
        set(df_in.columns) - set(fld_index + fld_value + fld_extra_fixed + fld_histo)
    )
    extra_sum = [col for col in fld_extra_other if col[:4] == "sum_"]
    extra_min = [col for col in fld_extra_other if col[:4] == "min_"]
    extra_max = [col for col in fld_extra_other if col[:4] == "max_"]
    extra_mean = [col for col in fld_extra_other if col[:5] == "mean_"]
    extra_last = list(
        set(fld_extra_other) - set(extra_sum + extra_min + extra_max + extra_mean)
    )

    # add fields to calculate mean values
    for col in extra_mean + fld_value:
        df_in[col + "_qua"] = df_in[col] * df_in["quantity"]

    # calculate DataFrame with new period
    grp = df_in.groupby(fld_index, sort=False)
    col_mean = [col + "_qua" for col in extra_mean + fld_value]
    grp_sum = grp[col_mean + extra_sum + ["quantity"]].sum()
    df_up = grp_sum[["quantity"]].copy()
    for col in extra_mean + fld_value:
        df_up[col] = grp_sum[col + "_qua"] / df_up["quantity"]
    for col in extra_sum:
        df_up[col] = grp_sum[col]
    grp_max = grp[extra_max + ["maxi"]].max()
    for col in extra_max + ["maxi"]:
        df_up[col] = grp_max[col]
    grp_min = grp[extra_min + ["mini"]].min()
    for col in extra_min + ["mini"]:
        df_up[col] = grp_min[col]
    grp_last = grp[extra_last + ["last"]].last()
    for col in extra_last + ["last"]:
        df_up[col] = grp_last[col]
    df_up["variance"] = 0.0
    pass  # variance calculation to add

    # add the historicization format
    df_up["extras"] = df_up[fld_extra_fixed + fld_extra_other].to_dict(orient="records")
    df_up["timestamp"] = timespan_up.start.isoformat()
    df_up["period"] = timespan_up.period

    return df_up.reset_index()[fld_index + fld_value + fld_extras + fld_histo]


def set_start_period(start: date, offset: int, period: IndicatorPeriod) -> datetime:
    """Return the start datetime of the period."""
    start_date = date.today() if start is None else start
    if offset:
        start_date += PeriodDuration[period.name].value * offset
    day_start = start_date.day
    month_start = start_date.month
    if offset:
        match period:
            case IndicatorPeriod.MONTH:
                day_start = 1
            case IndicatorPeriod.QUARTER:
                day_start = 1
                month_start = (start_date.month + 1) // 3 * 3 + 1
            case IndicatorPeriod.YEAR:
                day_start = 1
                month_start = 1
            case _:
                ...
    return datetime(start_date.year, month_start, day_start)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-up-{to_period.value}-{start:%y-%m-%d}",
)
def calculate(  # noqa: PLR0913
    environment: Environment,
    to_period: IndicatorPeriod,
    start: date | None = None,
    offset: int = -1,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    create_artifact: bool = False,
    persist: bool = False,
) -> pd.DataFrame:
    """Add an historicization with a new period."""
    init_period = set_start_period(start, offset, to_period)
    final_timespan = IndicatorTimeSpan(start=init_period, period=to_period)
    query_params = {
        "period": period.value,
        "start": init_period,
        "end": init_period + PeriodDuration[to_period.name].value,
    }
    query_template = Template(QUERY_HISTORICIZE)
    with Session(get_indicators_db_engine()) as session:
        histo_df = pd.read_sql_query(
            query_template.substitute(query_params), con=session.connection()
        )
    del histo_df["id"]
    histo_up_df = to_df_histo_up(histo_df, final_timespan)
    description = (
        f"up report at {final_timespan.start} (period: {final_timespan.period.value})"
    )
    flow_name = runtime.flow_run.name
    export_indicators(
        histo_up_df, environment, flow_name, description, create_artifact, persist
    )
    return histo_up_df
