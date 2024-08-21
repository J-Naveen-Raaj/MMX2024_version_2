# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd

from .calculate_attributions import get_multiplicative_attribution


def get_predictions(
    df,
    coefficients,
    model_variables,
    base_variables,
    control_variables,
    tp_variables,
    actual_var,
    dummy_vars=[],
    geo_var="X_GEO",
    date_var="X_DT",
    seg_var="X_SEG",
):
    df_copy = df.copy()

    if "I_INTERCEPT" in model_variables:
        df_copy["I_INTERCEPT"] = 1

    exceptions = ["I_INTERCEPT"]
    model_variables_exception = list(set(model_variables) - set(exceptions))

    # log transformation
    df_copy.loc[:, model_variables_exception] = np.log1p(
        df[model_variables_exception].astype(np.float32)
    )

    geo = df.loc[df.index[0], geo_var]
    predictions = (
        df_copy.loc[:, model_variables]
        .mul(coefficients.loc[geo, model_variables], axis=1)
        .astype(np.float32)
    )

    predictions[actual_var + "_predicted"] = predictions[model_variables].sum(axis=1)
    predictions["Base_Predictions"] = predictions[base_variables].sum(axis=1)
    predictions["Touchpoint_Predictions"] = predictions[tp_variables].sum(axis=1)
    predictions["Control_Predictions"] = (
        predictions[control_variables].sum(axis=1) if len(control_variables) != 0 else 0
    )

    # predictions['Touchpoint_Predictions'] = np.exp(predictions['Touchpoint_Predictions'])
    # predictions['Control_Predictions'] = np.exp(predictions['Control_Predictions'])

    predictions = predictions.set_index(df_copy.index)
    predictions[geo_var] = df[geo_var]
    predictions[seg_var] = df[seg_var]
    predictions[date_var] = df[date_var]

    return predictions


def get_contributions(
    predictions,
    coefficients,
    base_variables,
    control_variables,
    tp_variables,
    actual_var,
    remove_variables,
    scale_to_actual=True,
    geo_var="X_GEO",
    date_var="X_DT",
    seg_var="X_SEG",
):
    actuals_vs_preds_df = pd.DataFrame(
        {
            date_var: predictions[date_var],
            geo_var: predictions[geo_var],
            "preds": predictions[actual_var + "_predicted"],
            "actuals": predictions[actual_var + "_predicted"],
        },
        index=predictions.index,
    )

    model_variables = base_variables + control_variables + tp_variables

    coeff_matrix = coefficients.rename(
        columns={key: "beta_" + key for key in model_variables}
    ).reset_index()
    coeff_matrix.insert(0, geo_var, coeff_matrix.pop(geo_var))

    contribution_weekly_df = get_multiplicative_attribution(
        predictions,
        coeff_matrix,
        actuals_vs_preds_df,
        date_var,
        tp_variables + base_variables,
        control_variables,
    )
    contribution_weekly_df = contribution_weekly_df.rename(
        columns={"ac_" + key: key for key in model_variables}
    )
    contribution_weekly_df = contribution_weekly_df.rename(
        columns={"base": "I_INTERCEPT"}
    )
    # contribution_weekly_df["Base"] = (
    #     contribution_weekly_df[base_variables].sum(axis=1)
    #     if len(base_variables) != 0
    #     else 0
    # )
    # # contribution_weekly_df["Base"] = contribution_weekly_df["base"]
    # contribution_weekly_df["Control_Contribution"] = (
    #     contribution_weekly_df[control_variables].sum(axis=1)
    #     if len(control_variables) != 0
    #     else 0
    # )
    # contribution_weekly_df["Touchpoint_Contribution"] = (
    #     contribution_weekly_df[tp_variables].sum(axis=1)
    #     if len(tp_variables) != 0
    #     else 0
    # )

    contribution_weekly_df[seg_var] = predictions[seg_var]
    contribution_weekly_df[date_var] = predictions[date_var]
    contribution_weekly_df[geo_var] = predictions[geo_var]

    return contribution_weekly_df
