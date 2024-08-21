# -*- coding: utf-8 -*-
"""
This is the code for What-if Scenario.
Takes in the simulated spend and outputs touchpoint contribution and KPI outcome.
"""

import warnings

warnings.filterwarnings("ignore")
import os

import numpy as np
import pandas as pd

from app_server.MMOptim.config import REFERENCE_CALENDAR_YEAR
from app_server.MMOptim.constants import ALL_GEOS, ALL_SEGS
from app_server.WhatIF.whatif_input import get_input_data, get_variable_levels
from app_server.WhatIF.whatif_run import whatif_run


# %%
# Function called by front-end to generate what-if scenario output
def what_if_planner(simulated_spend, period_type, year):
    cur_dir = os.getcwd()
    # Get output for what_if run
    (
        main_data,
        distribution_ratios_df,
        mktg_sp_cols,
        spend_tp_mapping,
        var_type_dict,
        dependent_variables,
        segments,
        model_coeffs,
        ratio_table,
        adstock_variables_EX,
        adstock_variables_NTF,
        media_inflation_data,
        min_max_dict,
        spend_variables,
        control_mapping,
        seasonality,
        calendar,
    ) = get_input_data()

    os.chdir(cur_dir)

    # If spend is in wide format,convert from wide to long format
    # try:
    #     simulated_spend = convert_wide_to_long_format(simulated_spend)
    # except:
    #     simulated_spend = simulated_spend.copy()

    # Get the final output,data with updated spends from simulated spends
    final_output, data_simulated = whatif_run(
        main_data.copy(),
        distribution_ratios_df,
        simulated_spend,
        var_type_dict,
        model_coeffs,
        ratio_table,
        adstock_variables_EX,
        adstock_variables_NTF,
        media_inflation_data,
        min_max_dict,
        spend_variables,
        seasonality,
        control_mapping,
        calendar,
        spend_tp_mapping,
        year,
    )

    # Formatting the final output dataframe
    final_output["X_DT"] = pd.to_datetime(
        final_output["X_DT"], infer_datetime_format=True
    )
    final_output.sort_values(["X_DT", "X_SEG", "X_GEO"], inplace=True)
    final_output = pd.merge(
        final_output, calendar, left_on=["X_DT"], right_on=["Week end Date"]
    )

    final_output.columns = [col.lower() for col in final_output.columns]
    final_output.rename(
        {"x_seg": "segment", "variable": "node_name"}, axis=1, inplace=True
    )
    final_group_cols = ["outcome", "segment", "year", "quarter", "month", "node_name"]
    final_output = final_output.groupby(final_group_cols).aggregate({"value": sum})
    final_output.reset_index(inplace=True)
    period_map = {1: 1, 2: 1, 3: 2, 4: 2}
    final_output["halfyear"] = final_output["quarter"].map(period_map)

    # Creating a column to differentiate between variables contributing to
    # control and marketing attributions

    final_output["Attribution_Type"] = "MarketingAttribution"
    ext_value = pd.Series(
        ["ExternalAttribution" for _ in range(final_output.shape[0])],
        index=final_output.index,
    )
    final_output["Attribution_Type"] = final_output["Attribution_Type"].where(
        final_output["node_name"].str.startswith("M_"),
        ext_value.where(
            final_output["node_name"].str.startswith("E_"), "BaseAttribution"
        ),
    )
    # final_output["Attribution_Type"] = ["MarketingAttribution" if x.startswith(("PRO_","M_")) else "BaseAttribution" for x in final_output["node_name"]]
    #
    # Optimisation scenario outcome data template
    optimization_scenario_outcome = pd.DataFrame(
        columns=[
            "Outcome",
            "Segment",
            "BaseAttribution",
            "MarketingAttribution",
            "ExternalAttribution",
        ]
    )

    # Get final output by outcome, segment and attribution type
    final_output_by_group = pd.DataFrame(
        final_output.groupby(["outcome", "segment", "Attribution_Type"])["value"].sum()
    )
    final_output_by_group.reset_index(drop=False, inplace=True)
    # Get the data in optimization scenario outcome data format
    optimization_scenario_outcome = final_output_by_group.pivot_table(
        index=["outcome", "segment"], columns="Attribution_Type", values="value"
    )
    optimization_scenario_outcome.reset_index(drop=False, inplace=True)

    # Drop the extra column added from final dataframe
    final_output.drop(["Attribution_Type"], axis=1, inplace=True)

    ## Adding spend_value to final_output corresponding to node_name X segment X month
    variable_levels = get_variable_levels()
    spend_cols = list(set(mktg_sp_cols).intersection(set(final_output.node_name)))

    # Compute Spend Scaling Factor
    spend_scaling_factor = len(ALL_SEGS) ** (1 - variable_levels["Vary_by_SEG"]) * len(
        ALL_GEOS
    ) ** (1 - variable_levels["Vary_by_GEO"])
    spend_scaling_factor = pd.Series(
        spend_scaling_factor.values, index=variable_levels.index
    )
    # Get spend_scaling_factor for spends cols only
    spend_scaling_factor = spend_scaling_factor[
        spend_scaling_factor.index.isin(spend_cols)
    ]

    # def get_spend_totals(data, spend_vars, spend_scaling_factor):
    #     """
    #     Get marketing spend totals for a given data and variable levels
    #     """
    #     cols = set(spend_vars).intersection(set(data.columns))
    #     cols=list(cols)
    #     spend_totals = data[cols].sum(axis=0)
    #     if spend_scaling_factor is not None:
    #         spend_totals /= spend_scaling_factor
    #     return spend_totals

    group_cols = ["X_QTR", "X_MONTH", "X_DT", "X_SEG", "X_GEO"]
    # data_grouped = data_simulated.groupby(group_cols).apply(lambda x: get_spend_totals(x, spend_cols, spend_scaling_factor))
    data_grouped_long = data_simulated.melt(id_vars=group_cols)
    data_grouped_long.rename(columns={"value": "spend_value"}, inplace=True)
    data_grouped_long = (
        data_grouped_long.groupby(["X_QTR", "X_MONTH", "variable"])["spend_value"]
        .sum()
        .reset_index()
    )

    final_output["X_QTR"] = final_output["quarter"].astype(int)
    final_output = final_output.merge(
        data_grouped_long,
        left_on=["X_QTR", "month", "node_name"],
        right_on=["X_QTR", "X_MONTH", "variable"],
        how="left",
    )
    final_output.drop(["X_QTR", "X_MONTH", "variable"], axis=1, inplace=True)
    # Fill spends for control variable as 0
    final_output.fillna(0, inplace=True)

    return final_output, optimization_scenario_outcome
