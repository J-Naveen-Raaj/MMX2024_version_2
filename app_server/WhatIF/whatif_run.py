# import os
import time

import pandas as pd

from app_server.MMOptim.config import REFERENCE_CALENDAR_YEAR
from app_server.MMOptim.constants import ALL_SEGS, OUTCOME_VARS
from app_server.WhatIF.whatif_calculation import get_contributions, get_predictions
from app_server.WhatIF.whatif_transform import (
    calculate_adstock,
    calculate_lag,
    calculate_s_curve,
    get_data_from_spend_plan,
)

"""
This file runs the whatif for a given spend plan in long format

"""

# %%
def add_control_vars_to_data(main_data, mktg_data):
    """
    This function replaces simulated data in master data
    """

    index_cols = ["X_SEG", "X_GEO", "X_DT"]
    try:
        main_data.set_index(index_cols, inplace=True)
        mktg_data.set_index(index_cols, inplace=True)
    except Exception as e:
        print("Cannot set index in dataset", e)

    mktg_data_cols = set(mktg_data.columns)
    main_data_cols = set(main_data.columns)

    common_cols = mktg_data_cols.intersection(main_data_cols)
    extra_cols = list(mktg_data_cols - common_cols)
    common_cols = list(common_cols)

    main_data.loc[mktg_data.index, common_cols] = mktg_data[common_cols].values

    if len(extra_cols) > 0:
        for col in extra_cols:
            main_data[col] = 0
            main_data.loc[mktg_data.index, col] = mktg_data[col].values

    main_data.reset_index(inplace=True)
    mktg_data.reset_index(inplace=True)

    return main_data


# %%
def get_variable_lists_from_coeffs(coefficients, var_type_dict):
    """
    Finding the different variables and their types, present in the model
    """
    model_variables = list(coefficients.columns)
    dummy_variables = [col for col in model_variables if col.startswith("D_")]
    base_variables = [col for col in model_variables if col in var_type_dict["Base"]]
    base_variables = list(set(base_variables + dummy_variables))
    control_variables = [
        col for col in model_variables if col in var_type_dict["Control"]
    ]
    tp_variables = [
        col for col in model_variables if col in var_type_dict["Touchpoint"]
    ]

    return (
        model_variables,
        dummy_variables,
        base_variables,
        control_variables,
        tp_variables,
    )


# %%
def get_outcome_by_dv_seg(
    dv,
    seg,
    main_data,
    year,
    model_coeffs,
    spend_variables,
    control_mapping,
    calendar,
    var_type_dict,
    spend_tp_mapping,
):
    print(dv + " - " + seg)
    # Filter data for Segment & Year
    data = main_data[
        (main_data.X_SEG == "Rakuten") & (main_data["X_YEAR"] == year)
    ].reset_index(drop=True)
    # Get min_max data for required segment

    # Sort data by id columns
    id_cols = ["X_DT", "X_SEG", "X_GEO", "X_QTR", "X_MONTH"]

    data.sort_values(by=[col for col in data.columns if col in id_cols], inplace=True)
    # Fetching the coefficients for each variable (from model results)
    mask = (model_coeffs["outcome"] == dv) & (model_coeffs["X_SEG"] == "Rakuten")
    model_coeffs = model_coeffs.loc[mask]
    model_coeffs.drop(["X_GEO", "outcome"], axis=1)
    coefficients = model_coeffs.pivot_table(
        index="X_GEO", columns="variable", values="value", aggfunc="mean"
    )

    model_vars = list(coefficients.columns)
    map_dict = dict(zip(spend_tp_mapping.Variable, spend_tp_mapping.Spend_Variable))
    model_vars_root = list(pd.Series(model_vars).map(map_dict))
    sp_vars_not_in_modelling = list(
        set(spend_variables["Spend Variable"]) - set(model_vars_root)
    )

    # Adding Touchpoints not present in model with coefficients data as Zero
    print(
        "The following variables are added to the coefficents file: \n",
        sp_vars_not_in_modelling,
    )
    for var in sp_vars_not_in_modelling:
        coefficients[var] = 0

    # Printing model variables not present in the main dataset (need to create these variables)
    no_var_data = list(set(coefficients.columns) - set(data.columns))
    print("The following variables are missing from the dataset: \n", no_var_data)
    for var in no_var_data:
        if var != "I_INTERCEPT":
            data[var] = 0

    # Get list of variables
    (
        model_variables,
        dummy_variables,
        base_variables,
        control_variables,
        tp_variables,
    ) = get_variable_lists_from_coeffs(coefficients, var_type_dict)

    start_time = time.time()
    predictions = get_predictions(
        data.copy(),
        coefficients,
        model_variables,
        base_variables,
        control_variables,
        tp_variables,
        actual_var=dv,
        dummy_vars=dummy_variables,
        geo_var="X_GEO",
        date_var="X_DT",
        seg_var="X_SEG",
    )

    end_time = time.time()

    print("Predictions Time: ", end_time - start_time)

    # Reset the index
    predictions.reset_index(drop=True, inplace=True)

    start_time = time.time()
    # Contributions Module
    contributions = get_contributions(
        predictions,
        coefficients,
        base_variables,
        control_variables,
        tp_variables,
        actual_var=dv,
        remove_variables=base_variables,
        scale_to_actual=False,
        geo_var="X_GEO",
        date_var="X_DT",
        seg_var="X_SEG",
    )

    end_time = time.time()

    print("Contributions Time:", end_time - start_time)

    # Reset the index
    contributions.reset_index(drop=True, inplace=True)

    contrib_id_vars = ["X_SEG", "X_GEO", "X_DT"]
    contrib_value_vars = control_variables + tp_variables + base_variables
    contributions_long = pd.melt(
        contributions,
        id_vars=contrib_id_vars,
        value_vars=contrib_value_vars,
        var_name="variable",
    )
    contributions_long = (
        contributions_long.groupby(by=contrib_id_vars + ["variable"])
        .aggregate({"value": sum})
        .reset_index()
    )

    # Creating dictionary for touchpoint and control variable to map variables to their root variables
    map_dict = dict(zip(spend_tp_mapping.Variable, spend_tp_mapping.Spend_Variable))
    missing_control = set(control_variables) - set(control_mapping["Variable"])

    # Check to identify if a particular variable is missing from the Static file  "Control_Mapping"
    if len(missing_control) > 0:
        print(
            "Model Control Variables found missing in 'Control Mapping' File:",
            missing_control,
        )

    mask = contributions_long["variable"].str.startswith("I_")
    base_variables_dict = (
        contributions_long.assign(duplicate=contributions_long["variable"])
        .loc[mask]
        .groupby(["variable"])["variable"]
        .first()
        .to_dict()
    )
    control_variables_dict = dict(
        zip(control_mapping.Variable, control_mapping.Root_Variable)
    )
    map_dict.update(base_variables_dict)
    map_dict.update(control_variables_dict)

    contributions_long["variable"] = contributions_long["variable"].map(map_dict)
    contributions_long = (
        contributions_long.groupby(by=["X_GEO", "X_DT", "X_SEG", "variable"])
        .aggregate({"value": sum})
        .reset_index()
    )
    contributions_long["outcome"] = dv

    return contributions_long


def add_seasonality_vars(main_data, seasonality, target):
    seasonality = seasonality.loc[seasonality["outcome"] == target]
    main_data["month"] = pd.to_datetime(main_data["X_DT"]).dt.month
    main_data = pd.merge(main_data, seasonality, on="month")
    return main_data


def mean_scaling(main_data, min_max_mean):
    for key, val in min_max_mean.items():
        outcome_mask = main_data["outcome"] == key
        mean_ = val.set_index("Variable")
        main_data.loc[outcome_mask, val["Variable"]] = (
            main_data.loc[outcome_mask, val["Variable"]] / mean_["mean"]
        )
    return main_data


def transform_with_mktg(main_data, transform_variables, min_max_mean):
    main_data = calculate_adstock(main_data, transform_variables)
    main_data = calculate_lag(main_data, transform_variables)
    main_data = calculate_s_curve(main_data, transform_variables)
    main_data = mean_scaling(main_data, min_max_mean)
    return main_data


# %%
def whatif_run(
    main_data,
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
    dependent_variables=OUTCOME_VARS,
    segments=ALL_SEGS,
):
    ratio_year = REFERENCE_CALENDAR_YEAR

    simulated_spend_EX = simulated_spend.copy()
    simulated_spend_NTF = simulated_spend.copy()

    # Get new data for both simulated spend and threshold spend
    data_simulated_EX, data_simulated_spend_EX = get_data_from_spend_plan(
        simulated_spend_EX,
        distribution_ratios_df,
        spend_tp_mapping,
        ratio_table,
        calendar,
        year,
        ratio_year,
        media_inflation_data,
    )

    data_simulated_NTF, data_simulated_spend_NTF = get_data_from_spend_plan(
        simulated_spend_NTF,
        distribution_ratios_df,
        spend_tp_mapping,
        ratio_table,
        calendar,
        year,
        ratio_year,
        media_inflation_data,
    )

    data_simulated_EX = data_simulated_EX.fillna(0)
    data_simulated_NTF = data_simulated_NTF.fillna(0)

    # Replaces marketing data in main data with new data
    main_data_EX = add_control_vars_to_data(main_data, data_simulated_EX)
    main_data_NTF = add_control_vars_to_data(main_data, data_simulated_NTF)

    main_data_EX = add_seasonality_vars(main_data_EX, seasonality, "outcome2")
    main_data_NTF = add_seasonality_vars(main_data_NTF, seasonality, "outcome1")

    main_data_EX = transform_with_mktg(main_data_EX, adstock_variables_EX, min_max_dict)
    main_data_NTF = transform_with_mktg(
        main_data_NTF, adstock_variables_NTF, min_max_dict
    )

    final_output = pd.DataFrame()

    for dv in dependent_variables:
        for seg in segments:
            if dv == "outcome2":
                contributions_long = get_outcome_by_dv_seg(
                    dv,
                    seg,
                    main_data_EX,
                    year,
                    model_coeffs,
                    spend_variables,
                    control_mapping,
                    calendar,
                    var_type_dict,
                    spend_tp_mapping,
                )
            else:
                contributions_long = get_outcome_by_dv_seg(
                    dv,
                    seg,
                    main_data_NTF,
                    year,
                    model_coeffs,
                    spend_variables,
                    control_mapping,
                    calendar,
                    var_type_dict,
                    spend_tp_mapping,
                )

            final_output = pd.concat([final_output, contributions_long], axis=0)

    return final_output, data_simulated_spend_NTF
