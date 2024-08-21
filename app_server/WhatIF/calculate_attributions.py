from typing import List

import numpy as np
import pandas as pd


def _combine_marketing_and_control_vars(
    transformed_data: pd.DataFrame, marketing_vars: List[str], control_vars: List[str]
) -> pd.DataFrame:
    """
    Combine marketing and control variables with transformed data.

    Parameters
    ----------
    transformed_data : pd.DataFrame
        Transformed data used to train the model.
    marketing_vars : List[str]
        List of marketing variables.
    control_vars : List[str]
        List of control variables.

    Returns
    -------
    pd.DataFrame
        DataFrame with combined marketing and control variables.
    """
    all_idvs = marketing_vars + control_vars
    contribution_df = transformed_data.filter(all_idvs)  # .add_prefix("t_")
    return contribution_df


def _merge_data_with_coefficients(
    contribution_df: pd.DataFrame,
    transformed_data: pd.DataFrame,
    coeff_matrix: pd.DataFrame,
    date_col: str,
) -> pd.DataFrame:
    """
    Merge contribution data with coefficient matrix.

    Parameters
    ----------
    contribution_df : pd.DataFrame
        DataFrame with combined marketing and control variables.
    transformed_data : pd.DataFrame
        Transformed data used to train the model.
    coeff_matrix : pd.DataFrame
        DataFrame containing the feature coefficients generated by training a model.
    date_col : str
        Name of the date column.

    Returns
    -------
    pd.DataFrame
        Merged DataFrame.
    """
    contribution_df.insert(0, date_col, transformed_data[date_col])
    group_col = coeff_matrix.columns[0]
    contribution_df.insert(1, group_col, transformed_data[group_col])
    return (
        pd.merge(contribution_df, coeff_matrix, on=group_col, how="left")
        .sort_values(by=date_col)
        .reset_index(drop=True)
    )


def _calculate_beta_into_x(
    contribution_df: pd.DataFrame, marketing_vars: List[str], control_vars: List[str]
) -> pd.DataFrame:
    """
    Calculate beta into x.

    Parameters
    ----------
    contribution_df : pd.DataFrame
        Merged DataFrame.
    marketing_vars : List[str]
        List of marketing variables.
    control_vars : List[str]
        List of control variables.

    Returns
    -------
    pd.DataFrame
        DataFrame with calculated values.
    """
    # beta_matrix = contribution_df.filter([f"beta_{col}" for col in marketing_vars + control_vars]).values
    # x_matrix = contribution_df.filter([f"t_{col}" for col in marketing_vars + control_vars]).values
    # e_beta_into_x = np.exp(np.multiply(beta_matrix, x_matrix))
    e_beta_into_x = np.exp(contribution_df[marketing_vars + control_vars])
    # column_names = [f"e_{col}_into_beta" for col in marketing_vars + control_vars]
    # intermediate_df = pd.DataFrame(e_beta_into_x, columns=column_names)
    # e_beta_into_x = pd.read_excel(r"C:\Users\roshan.hande\Projects\Rakuten Americas Phase-2\Reports\calculated contributions.xlsx")
    column_rename = {col: f"e_{col}_into_beta" for col in marketing_vars + control_vars}
    intermediate_df = e_beta_into_x.rename(columns=column_rename)
    return pd.concat([contribution_df[["X_GEO", "X_DT"]], intermediate_df], axis=1)


def _calculate_y_values(
    contribution_df: pd.DataFrame,
    act_vs_preds: pd.DataFrame,
    control_vars: List[str],
    date_col: str,
    group_col: str,
) -> pd.DataFrame:
    """
    Calculate y, y_control, and y_mkt values.

    Parameters
    ----------
    contribution_df : pd.DataFrame
        DataFrame with calculated values.
    act_vs_preds : pd.DataFrame
        DataFrame containing actual vs predicted values.
    control_vars : List[str]
        List of control variables.
    date_col : str
        Name of the date column.
    group_col : str
        Name of the group column.

    Returns
    -------
    pd.DataFrame
        DataFrame with calculated values.
    """
    act_vs_preds_subset = act_vs_preds[[date_col, group_col, "preds", "actuals"]]
    contribution_df[["preds", "actuals"]] = np.exp(
        contribution_df.merge(
            act_vs_preds_subset, on=[date_col, group_col], how="left"
        )[["preds", "actuals"]]
    )
    contribution_df["y_control"] = (
        np.prod(
            contribution_df.filter([f"e_{col}_into_beta" for col in control_vars]),
            axis=1,
        )
        # * contribution_df["e_intercept"]
        * contribution_df["e_I_INTERCEPT_into_beta"]
    )
    contribution_df["y_mkt"] = contribution_df["preds"] - contribution_df["y_control"]
    return contribution_df


def _calculate_raw_contributions(
    contribution_df: pd.DataFrame, marketing_vars: List[str], control_vars: List[str]
) -> pd.DataFrame:
    """
    Calculate raw contributions for marketing and control variables.

    Parameters
    ----------
    contribution_df : pd.DataFrame
        DataFrame with calculated values.
    marketing_vars : List[str]
        List of marketing variables.
    control_vars : List[str]
        List of control variables.

    Returns
    -------
    pd.DataFrame
        DataFrame with calculated values.
    """
    marketing_vars = list(set(marketing_vars) - set(["I_INTERCEPT"]))
    for col in control_vars:
        contribution_df[f"rc_{col}"] = contribution_df["y_control"] * (
            1 - 1 / contribution_df[f"e_{col}_into_beta"]
        )

    contribution_df["sum_control"] = contribution_df.filter(
        [f"rc_{col}" for col in control_vars]
    ).sum(axis=1)

    for col in marketing_vars:
        contribution_df[f"rc_{col}"] = contribution_df["y_mkt"] * (
            1 - 1 / contribution_df[f"e_{col}_into_beta"]
        )

    contribution_df["sum_mkt"] = contribution_df.filter(
        [f"rc_{col}" for col in marketing_vars]
    ).sum(axis=1)
    return contribution_df


def _calculate_actual_contributions(
    contribution_df: pd.DataFrame,
    marketing_vars: List[str],
    control_vars: List[str],
    date_col: str,
    group_col: str,
) -> pd.DataFrame:
    """
    Calculate actual contributions for marketing and control variables.

    Parameters
    ----------
    contribution_df : pd.DataFrame
        DataFrame with calculated values.
    marketing_vars : List[str]
        List of marketing variables.
    control_vars : List[str]
        List of control variables.
    date_col : str
        Name of the date column.
    group_col : str
        Name of the group column.

    Returns
    -------
    pd.DataFrame
        DataFrame with calculated values.
    """
    marketing_vars = list(set(marketing_vars) - set(["I_INTERCEPT"]))
    for col in control_vars:
        contribution_df[f"ac_{col}"] = (
            contribution_df[f"rc_{col}"]
            * contribution_df["y_control"]
            / contribution_df["sum_control"]
        )

    for col in marketing_vars:
        contribution_df[f"ac_{col}"] = (
            contribution_df[f"rc_{col}"]
            * contribution_df["y_mkt"]
            / contribution_df["sum_mkt"]
        )

    #     contribution_df["actuals_without_intercept"] = contribution_df["actuals"] - contribution_df["e_intercept"]

    #     for col in marketing_vars + control_vars:
    #         contribution_df[f"ac_{col}"] = (
    #             contribution_df[f"ac_{col}"] * contribution_df["actuals_without_intercept"] / contribution_df["preds"]
    #         )

    contribution_df["preds_without_intercept"] = (
        contribution_df["preds"] - contribution_df["e_I_INTERCEPT_into_beta"]
    )

    for col in marketing_vars + control_vars:
        contribution_df[f"ac_{col}"] = (
            contribution_df[f"ac_{col}"]
            * contribution_df["preds_without_intercept"]
            / contribution_df["preds"]
        )

    final_contrib_df = contribution_df.filter(
        [date_col, group_col]
        + ["e_I_INTERCEPT_into_beta"]
        + [f"ac_{col}" for col in marketing_vars + control_vars]
    ).rename(columns={"e_I_INTERCEPT_into_beta": "base"})
    return final_contrib_df


def get_multiplicative_attribution(
    data: pd.DataFrame,
    coeff_matrix: pd.DataFrame,
    act_vs_preds: pd.DataFrame,
    date_col: str,
    marketing_vars: List[str],
    control_vars: List[str],
) -> pd.DataFrame:
    """
    Compute multiplicative attribution.

    Parameters
    ----------
    data : pd.DataFrame
        Data used to train the model.
    coeff_matrix : pd.DataFrame
        DataFrame containing the feature coefficients generated by training a model.
    act_vs_preds : pd.DataFrame
        DataFrame containing actual vs predicted values. This dataframe can be obtained when training a model or by using the coefficient dataframe.
    date_col : str
        Name of the date column.
    marketing_vars : List[str]
        List of marketing variables.
    control_vars : List[str]
        List of control variables.

    Returns
    -------
    pd.DataFrame
        DataFrame with the final contributions.
    """
    group_col = coeff_matrix.columns[0]
    contribution_df = _combine_marketing_and_control_vars(
        data, marketing_vars, control_vars
    )
    contribution_df = _merge_data_with_coefficients(
        contribution_df, data, coeff_matrix, date_col
    )
    contribution_df = _calculate_beta_into_x(
        contribution_df, marketing_vars, control_vars
    )
    contribution_df = _calculate_y_values(
        contribution_df, act_vs_preds, control_vars, date_col, group_col
    )
    contribution_df = _calculate_raw_contributions(
        contribution_df, marketing_vars, control_vars
    )
    final_contrib_df = _calculate_actual_contributions(
        contribution_df, marketing_vars, control_vars, date_col, group_col
    )
    return final_contrib_df
