"""QualiCharge prefect indicators: historicization up."""

import json
from datetime import datetime, timedelta
from string import Template

import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, dialects, types
from sqlalchemy.engine import Connection, Engine

from indicators.models import (
    Indicator,
    IndicatorPeriod,
    IndicatorTimeSpan,
    Level,
    PeriodDuration,
)


def to_df_histo_up(
    indic: pd.DataFrame, timest: datetime, period: IndicatorPeriod
) -> pd.DataFrame:
    """Return a converted historicization for a new period."""
    index = ["code", "level", "target", "category"]
    histo = ["period", "timestamp"]
    value = ["value"]
    add_val = ["quantity", "mini", "maxi", "last", "variance"]
    fixe = index + value + add_val + histo

    # normalize the DataFrame
    df = indic.sort_values(by="timestamp").reset_index(drop=True)
    df["category"] = df["category"].fillna(
        " "
    )  # groupby daesn't work well with NA values
    df["value"] = df["value"].astype("float")
    if "extras" in df.columns:
        df = pd.concat([df, pd.json_normalize(df["extras"])], axis=1)
        del df["extras"]
    if "quantity" not in df.columns:
        df["quantity"] = 1
    if (df["quantity"] == 1).all():
        df["mini"] = df["value"]
        df["maxi"] = df["value"]
        df["last"] = df["value"]
        df["variance"] = 0.0

    # decode specific additional values
    add_col = list(set(df.columns) - set(fixe))
    add_col_sum = [col for col in add_col if col[:4] == "sum_"]
    add_col_min = [col for col in add_col if col[:4] == "min_"]
    add_col_max = [col for col in add_col if col[:4] == "max_"]
    add_col_mean = [col for col in add_col if col[:5] == "mean_"]
    add_col_last = list(
        set(add_col) - set(add_col_sum + add_col_min + add_col_max + add_col_mean)
    )

    # add fields to calculate mean values
    for col in add_col_mean + ["value"]:
        df[col + "_qua"] = df[col] * df["quantity"]

    # group the DataFrame
    grp = df.groupby(index, sort=False)
    col_mean = [col + "_qua" for col in add_col_mean + value]
    grp_sum = grp[col_mean + add_col_sum + ["quantity"]].sum()
    df_up = grp_sum[["quantity"]].copy()
    for col in add_col_mean + ["value"]:
        df_up[col] = grp_sum[col + "_qua"] / df_up["quantity"]
    for col in add_col_sum:
        df_up[col] = grp_sum[col]
    grp_max = grp[add_col_max + ["maxi"]].max()
    for col in add_col_max + ["maxi"]:
        df_up[col] = grp_max[col]
    grp_min = grp[add_col_min + ["mini"]].min()
    for col in add_col_min + ["mini"]:
        df_up[col] = grp_min[col]
    grp_last = grp[add_col_last + ["last"]].last()
    for col in add_col_last + ["last"]:
        df_up[col] = grp_last[col]
    df_up["variance"] = 0.0
    pass  # variance calculation to add

    # add the historicization format
    df_up["extras"] = df_up[add_val + add_col].to_dict(orient="records")
    df_up["timestamp"] = timest
    df_up["period"] = period.value

    return df_up.reset_index()[index + value + ["extras"] + histo]
