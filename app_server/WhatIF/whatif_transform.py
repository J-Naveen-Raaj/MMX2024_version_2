# CODE TO CREATE A NEW DATASET ACCORDING TO SIMULATED SPEND

import math
import re
from datetime import datetime

import numpy as np
import pandas as pd
from pandas.tseries.frequencies import to_offset
from pandas.tseries.offsets import DateOffset

from app_server.MMOptim.config import WHATIF_YEAR
from app_server.MMOptim.constants import DATE_COL, GEO_COL, MONTHS, SEG_COL
from app_server.WhatIF.ad_stock_module import apply_adstock


# %%
def format_spend_plan(simulated_spend):
    try:
        simulated_spend.drop("Variable Description", axis=1, inplace=True)
    except Exception:
        pass

    simulated_spend = pd.melt(
        simulated_spend, id_vars="Variable Name", var_name="X_QTR", value_name="value"
    )

    simulated_spend["X_QTR"] = (
        simulated_spend["X_QTR"].str.replace("Q", "").astype("int64")
    )
    simulated_spend.rename(columns={"Variable Name": "Spend_Variable"}, inplace=True)

    return simulated_spend


# %%
def get_mktg_data_from_spend_data(
    simulated_spend, spend_tp_mapping, ratio_data, media_inflation_data
):
    # Get impression and clicks for corresponding spend variable

    mktg_data = pd.merge(simulated_spend, spend_tp_mapping, on="Spend_Variable").drop(
        "Spend_Variable", axis=1
    )

    # Map the spend variable name with their corresponding spends and impressions
    # and get the current ratio of these variables from ratio table
    media_inflation_mapped_data = pd.merge(
        media_inflation_data,
        spend_tp_mapping,
        left_on="variable_name",
        right_on="Spend_Variable",
    )
    media_inflation_mapped_data = pd.merge(
        media_inflation_mapped_data, ratio_data, on="Variable"
    )

    # Filter for impressions and click
    tp_suffixes = ("IMP", "CLK", "INST")
    map_var = media_inflation_mapped_data["Variable"]
    mask = map_var.str.endswith(tp_suffixes)
    media_inflation_mapped_data = media_inflation_mapped_data.loc[mask]

    # Calculate the new ratio based on inflation factor
    media_inflation_mapped_data["New_Ratio"] = 1 / (
        (1 / media_inflation_mapped_data["Ratio"])
        * ((100 + media_inflation_mapped_data["Inflation_Factor"]) / 100)
    )

    # Place the new ratio values in the ratio table for these variables
    media_inflation_mapped_data.set_index(["X_GEO", "X_SEG", "Variable"], inplace=True)
    ratio_data.set_index(["X_GEO", "X_SEG", "Variable"], inplace=True)
    ratio_data.loc[media_inflation_mapped_data.index, "Ratio"] = (
        media_inflation_mapped_data["New_Ratio"]
    )
    ratio_data.reset_index(drop=False, inplace=True)

    # Merge with ratio_table to get Seg X Geo ratio
    mktg_data_converted = pd.merge(mktg_data, ratio_data, on=["Variable"])

    mktg_data_converted["value"] *= mktg_data_converted["Ratio"]

    mktg_data_converted.drop("Ratio", axis=1, inplace=True)

    mktg_data["X_SEG"] = mktg_data_converted["X_SEG"]
    mktg_data["X_GEO"] = mktg_data_converted["X_GEO"]

    return mktg_data_converted, mktg_data


def get_weekly_level_mktg_data_imp(mktg_data, calendar, period_col):
    calendar = calendar.copy()
    calendar["X_YEAR"] = WHATIF_YEAR
    cal_week_count = calendar.assign(
        week_count=(
            calendar.assign(DT=calendar["X_DT"])
            .groupby(period_col)["DT"]
            .transform("count")
        )
    )
    mktg_data_week = pd.merge(mktg_data, cal_week_count, on=[period_col], how="left")
    mktg_data_week["value"] = mktg_data_week["value"] / mktg_data_week["week_count"]
    mktg_data_week = mktg_data_week.rename(columns={"Variable": "variable"})
    mktg_data_week = pd.pivot_table(
        mktg_data_week,
        index=["X_DT", "X_MONTH", "X_QTR", "X_SEG", "X_GEO"],
        columns="variable",
        values="value",
    ).reset_index()
    return mktg_data_week


# %%
def lag_transform(ser: pd.Series, lag: int = 0):
    """
    shifts the ser with `lag`
    """
    return ser.shift(lag).fillna(0).values


def calculate_lag(mktg_data, lag_variables):
    mktg_data.sort_values(["X_SEG", "X_GEO", "X_DT"], inplace=True)
    mktg_data = mktg_data.reset_index(drop=True)
    grouped_data = mktg_data.groupby(["X_SEG", "X_GEO"])
    # ad_stock_variables["Original Variable"]=ad_stock_variables["Original Variable"].apply(lambda x:x if x.endswith("SP") else "-1")
    # ad_stock_variables=ad_stock_variables[ad_stock_variables["Original Variable"]!="-1"]
    for index, row in lag_variables.iterrows():
        # If half life is 0, then variable only has lag
        if row["lag"] == 0 or row["lag"] is None:
            mktg_data[row["Original Variable"]] = mktg_data[
                row["Original Variable"]
            ].values
            continue

        compiled_data = grouped_data.apply(
            lambda x: lag_transform(x[row["Original Variable"]], row["lag"])
        ).reset_index()
        temp_df = compiled_data.explode(0).reset_index(drop=True)

        mktg_data[row["Original Variable"]] = temp_df[0]
    return mktg_data


def s_curve_transform(ser: pd.Series, alpha: float, beta: float):
    """
    transforms ser using s curve based on `alpha` and `beta` parameter
    """
    return (alpha * (1 - np.exp(-1.0 * beta * ser))).values


def calculate_s_curve(mktg_data, s_curve_variables):
    mktg_data.sort_values(["X_SEG", "X_GEO", "X_DT"], inplace=True)
    mktg_data = mktg_data.reset_index(drop=True)
    grouped_data = mktg_data.groupby(["X_SEG", "X_GEO"])
    for index, row in s_curve_variables.iterrows():
        # If scurve is None, then copy variable as it is
        if row["scurve"] is None or pd.isna(row["scurve"]):
            mktg_data[row["Original Variable"]] = mktg_data[
                row["Original Variable"]
            ].values
            continue

        scurve_param_regex = re.compile(
            "Best alpha:(?P<alpha>[NAnoeE0-9.+-]*) Best beta:(?P<beta>[NAnoeE0-9.+-]*)"
        )
        res = scurve_param_regex.match(row["scurve"])
        # if row['scurve'] == "Best alpha:No Best beta:No":
        if res is None or (res["alpha"] == "No" and res["beta"] == "No"):
            mktg_data[row["Original Variable"]] = mktg_data[
                row["Original Variable"]
            ].values
            continue

        try:
            alpha = float(res["alpha"])
        except ValueError:
            print("alpha parameter not a number")
            raise
        try:
            beta = float(res["beta"])
        except ValueError:
            print("beta parameter not a number")
            raise

        print(row["Original Variable"], alpha, beta)
        compiled_data = grouped_data.apply(
            lambda x: s_curve_transform(
                x[row["Original Variable"]].astype(np.float32), alpha, beta
            )
        ).reset_index()
        temp_df = compiled_data.explode(0).reset_index(drop=True)
        mktg_data[row["Original Variable"]] = temp_df[0]
    return mktg_data


# %%
def calculate_adstock(mktg_data, ad_stock_variables):
    mktg_data.sort_values(["X_SEG", "X_GEO", "X_DT"], inplace=True)
    mktg_data = mktg_data.reset_index(drop=True)
    grouped_data = mktg_data.groupby(["X_SEG", "X_GEO"])
    for index, row in ad_stock_variables.iterrows():
        # If half life is 0, then variable has no adstock
        if row["Ad-stock Half Life"] == 0 or row["Ad-stock Half Life"] is None:
            mktg_data[row["Original Variable"]] = mktg_data[
                row["Original Variable"]
            ].values
            continue

        compiled_data = grouped_data.apply(
            lambda x: apply_adstock(
                x[row["Original Variable"]],
                4,
                math.exp(math.log(0.5) / row["Ad-stock Half Life"]),
            )
            # lambda x: ad_stock(
            #    x[row["Original Variable"]], row["Ad-stock Half Life"], 4
            # )
        ).reset_index()
        temp_df = compiled_data.explode(0).reset_index(drop=True)
        mktg_data[row["Original Variable"]] = temp_df[0]
    return mktg_data


# %%
def format_spend_plan_what_if(simulated_spend, distribution_ratios_df):
    print("before total simulated spends", simulated_spend["spend_value"].sum())
    period_type = simulated_spend["period_type"].unique()
    if len(period_type) == 0:
        raise Exception(f"simulated spend missing granularity")
    if len(period_type) != 1:
        raise Exception(
            f"simulated spend contains more than one period granularity i.e {','.join(period_type)}"
        )
    if period_type == "monthly":
        period_col = "X_MONTH"
        simulated_spend[period_col] = (
            simulated_spend["period_name"]
            .replace({month: idx + 1 for idx, month in enumerate(MONTHS)})
            .replace({f"M{idx}": idx for idx in range(1, 13)})
            .replace({f"M_{idx}": idx for idx in range(1, 13)})
            .astype("int32")
        )
    elif period_type == "quarterly":
        period_col = "X_QTR"
        simulated_spend[period_col] = (
            simulated_spend["period_name"]
            .replace({f"Q{idx}": idx for idx in range(1, 5)})
            .astype("int32")
        )
        distribution_ratios_df = (
            distribution_ratios_df.groupby(["node_name", GEO_COL, SEG_COL, "MONTH"])
            .agg(SPENDS=pd.NamedAgg(column="SPENDS", aggfunc=sum))
            .unstack(level=[-2, -1])
            .fillna(1)
            .stack(level=[2, 1], dropna=False)
            .reset_index()
        )
        distribution_ratios_df["QUARTER"] = (
            distribution_ratios_df["MONTH"] - 1
        ) // 3 + 1
        distribution_ratios_df["QUARTER"] = (
            distribution_ratios_df["QUARTER"].map(int).astype("int32")
        )
        distribution_ratios_df["SPENDS"] = distribution_ratios_df["SPENDS"].replace(
            {0: 1}
        )
        distribution_ratios_df["ratio"] = distribution_ratios_df["SPENDS"].div(
            distribution_ratios_df.groupby(["node_name", GEO_COL, SEG_COL, "QUARTER"])[
                "SPENDS"
            ].transform(sum)
        )
        simulated_spend_distrib = pd.merge(
            distribution_ratios_df.drop(columns=["SPENDS"]),
            simulated_spend,
            left_on=["node_name", GEO_COL, "QUARTER"],
            right_on=["node_name", "geo", period_col],
            how="right",
        )
        simulated_spend_distrib["distrib_spend_value"] = (
            simulated_spend_distrib["spend_value"].fillna(0)
            * simulated_spend_distrib["ratio"]
        )
        period_col = "X_MONTH"
        simulated_spend = simulated_spend_distrib.loc[
            simulated_spend_distrib["MONTH"].notna(),
            [
                "period_name",
                "node_name",
                "distrib_spend_value",
                "geo",
                "MONTH",
            ],
        ]
        simulated_spend["period_type"] = "monthly"
        simulated_spend = simulated_spend.rename(
            columns={"MONTH": period_col, "distrib_spend_value": "spend_value"}
        )
    elif period_type == "weekly":
        period_col = "X_DT"
        week_regex = re.compile(
            "W_(?P<week_num>[0-9]{,2}) (?P<year>[0-9]{4})-(?P<month>[a-zA-Z]*)-(?P<week_end_date>[0-9]{,2})"
        )
        week_period = pd.json_normalize(
            simulated_spend["period_name"].map(
                lambda val: week_regex.match(val).groupdict()
            )
        )
        base_year = week_period["year"].unique()[0]
        base_year = int(base_year)
        weeks_of_base = pd.DataFrame(
            {
                "date": pd.date_range(
                    datetime(base_year, 1, 1), datetime(base_year, 12, 31)
                )
            }
        )
        weeks_of_base["count"] = 1
        freq = "W-SUN"
        weeks_of_base["week_end_date"] = weeks_of_base["date"] + to_offset(freq)
        weeks_of_base["days_count"] = weeks_of_base.groupby(["week_end_date"])[
            "count"
        ].transform(sum)
        weeks_of_base["week_period_repr"] = (
            "W_"
            + weeks_of_base["week_end_date"].dt.isocalendar().week.astype(str)
            + " "
            + weeks_of_base["week_end_date"].dt.strftime("%Y")
            + "-"
            + weeks_of_base["week_end_date"].dt.strftime("%b")
            + "-"
            + weeks_of_base["week_end_date"].dt.day.astype(str)
        )
        simulated_spend_daily = pd.merge(
            simulated_spend,
            weeks_of_base,
            left_on=["period_name"],
            right_on=["week_period_repr"],
            how="outer",
        )
        simulated_spend_daily["spend_value"] = (
            simulated_spend_daily["spend_value"] / simulated_spend_daily["days_count"]
        )
        simulated_spend_daily[period_col] = simulated_spend_daily["date"] + DateOffset(
            years=WHATIF_YEAR - base_year
        )
        simulated_spend = (
            simulated_spend_daily.groupby(
                ["node_name", "geo", pd.Grouper(key=period_col, freq=freq)]
            )
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )
    elif period_type == "yearly":
        period_col = "X_YEAR"
        simulated_spend[period_col] = WHATIF_YEAR
        distribution_ratios_df = (
            distribution_ratios_df.groupby(["node_name", GEO_COL, SEG_COL, "MONTH"])
            .agg(SPENDS=pd.NamedAgg(column="SPENDS", aggfunc=sum))
            .unstack(level=[-2, -1])
            .fillna(1)
            .stack(level=[2, 1], dropna=False)
            .reset_index()
        )
        distribution_ratios_df["YEAR"] = WHATIF_YEAR
        distribution_ratios_df["SPENDS"] = distribution_ratios_df["SPENDS"].replace(
            {0: 1}
        )
        distribution_ratios_df["ratio"] = distribution_ratios_df["SPENDS"].div(
            distribution_ratios_df.groupby(["node_name", GEO_COL, SEG_COL, "YEAR"])[
                "SPENDS"
            ].transform(sum)
        )
        simulated_spend_distrib = pd.merge(
            distribution_ratios_df.drop(columns=["SPENDS"]),
            simulated_spend,
            left_on=["node_name", GEO_COL, "YEAR"],
            right_on=["node_name", "geo", period_col],
            how="right",
        )
        simulated_spend_distrib["distrib_spend_value"] = (
            simulated_spend_distrib["spend_value"].fillna(0)
            * simulated_spend_distrib["ratio"]
        )
        period_col = "X_MONTH"
        simulated_spend = simulated_spend_distrib.loc[
            simulated_spend_distrib["MONTH"].notna(),
            [
                "period_name",
                "node_name",
                "distrib_spend_value",
                "geo",
                "MONTH",
            ],
        ]
        simulated_spend["period_type"] = "monthly"
        simulated_spend = simulated_spend.rename(
            columns={"MONTH": period_col, "distrib_spend_value": "spend_value"}
        )

    simulated_spend = simulated_spend[
        ["node_name", "geo", "spend_value", period_col]
    ].rename(
        columns={
            "node_name": "Spend_Variable",
            "spend_value": "value",
        }
    )
    simulated_spend = simulated_spend.dropna().reset_index(drop=True)
    return simulated_spend, period_col


# %%
def get_data_from_spend_plan(
    simulated_spend,
    distribution_ratios_df,
    spend_tp_mapping,
    ratio_table,
    calendar,
    year,
    ratio_year,
    media_inflation_data,
    run_type="what_if",
):
    calendar = calendar.loc[
        calendar["YEAR"] == year, ["Week end Date", "QUARTER", "MONTH", "YEAR"]
    ]
    calendar = calendar.rename(
        columns={
            "Week end Date": "X_DT",
            "QUARTER": "X_QTR",
            "MONTH": "X_MONTH",
            "YEAR": "X_YEAR",
        }
    )
    ratio_data = ratio_table[ratio_table["X_YEAR"] == ratio_year].drop("X_YEAR", axis=1)

    if run_type != "what_if":
        simulated_spend = format_spend_plan(simulated_spend)
    else:
        simulated_spend, period_col = format_spend_plan_what_if(
            simulated_spend, distribution_ratios_df
        )

    # Add Geo X Seg level to the mktg data (spend + impress)
    mktg_data, mktg_spend_data = get_mktg_data_from_spend_data(
        simulated_spend, spend_tp_mapping, ratio_data, media_inflation_data
    )

    # Convert mnthly, quarterly data to weekly level data by splitting them equally
    mktg_data = get_weekly_level_mktg_data_imp(mktg_data, calendar, period_col)
    mktg_spend_data = get_weekly_level_mktg_data_imp(
        mktg_spend_data, calendar, period_col
    )
    return mktg_data, mktg_spend_data
