import logging
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import regex as re
from pandas.tseries.frequencies import to_offset


def get_number_of_weeks(period_type, period_year, period):
    sdate = None
    edate = None

    if period_type == "QUARTER":
        if period == "Q1":
            sdate = date(period_year, 1, 1)
            edate = date(period_year, 3, 31)

        elif period == "Q2":
            sdate = date(period_year, 4, 1)
            edate = date(period_year, 6, 30)

        elif period == "Q3":
            sdate = date(period_year, 7, 1)
            edate = date(period_year, 9, 30)

        elif period == "Q4":
            sdate = date(period_year, 10, 1)
            edate = date(period_year, 12, 31)

    elif period_type == "MONTH":
        sdate = datetime.strptime(f"{period_year} {period} 01", "%Y %b %d")
        edate = sdate + to_offset("M")

    number_of_weeks = len(pd.date_range(sdate, edate, freq="w"))
    return number_of_weeks


def s_curve_transform(ser: pd.Series, alpha: float, beta: float):
    """
    transforms ser using s curve based on `alpha` and `beta` parameter
    """
    return (alpha * (1 - np.exp(-1.0 * beta * ser))).values


def transform(transformation_paremeters_df, dataset_df, idvs):
    transformed_df = dataset_df.copy()
    transformation_paremeters_df.fillna("", inplace=True)

    #  transformation
    i = 0
    for subchannel in list(transformation_paremeters_df["original_variable"]):
        if subchannel not in idvs:
            continue
        transformed_df[subchannel] = transformed_df[subchannel].astype("float")

        # Scurve
        s_parameter = transformation_paremeters_df.iloc[i, 4]
        alpha_beta = re.findall(r":([0-9.]+)", s_parameter)
        if len(alpha_beta) != 0:
            transformed_df[subchannel] = s_curve_transform(
                transformed_df[subchannel],
                alpha=float(alpha_beta[0]),
                beta=float(alpha_beta[1]),
            )

        i = i + 1

    return transformed_df


def log_transformation(data: pd.DataFrame, columns) -> pd.DataFrame:
    """Apply log(x + 1) transformation on selected columns of a given DataFrame.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame.
    columns : List[str]
        The list of column names to apply the log transformation.

    Returns
    -------
    pd.DataFrame
        The transformed DataFrame with log-transformed values in the selected columns.
    """
    transformed_data = data.copy()

    for col in columns:
        if col not in transformed_data.columns:
            logging.warning(f"Column {col} not present in the data.")
            continue

        transformed_data[col] = np.log1p(transformed_data[col])

    return transformed_data


def convert_spends_to_impression_clicks(spends_df, conversion_ratio_df):
    list_of_columns = list(spends_df.columns)
    for i in range(len(spends_df)):
        for j in range(spends_df.shape[1]):
            var = list_of_columns[j]

            if var not in list(conversion_ratio_df["Variable"].values):
                continue
            converstion_ratio = conversion_ratio_df[
                conversion_ratio_df["Variable"] == var
            ]["Ratio"].iloc[0]
            spends_df.iloc[i, j] = spends_df.iloc[i, j] * (converstion_ratio)

    return spends_df


def predict(data_df, idvs, coefficient_df):
    results = []
    for i in range(len(data_df)):
        prediction = 0  # coefficient_df.loc["Intercept", 0]
        for idv in idvs:
            if idv not in coefficient_df["variable"].values:
                continue
            coefficient = coefficient_df[coefficient_df["variable"] == idv][
                "value"
            ].iloc[0]
            value = data_df[idv].iloc[i]
            prediction = prediction + coefficient * value
        results.append(prediction)
    return results


def model_results(mean_scaling_df, data_df, coefficient_df, dv):
    scaled_df = data_df.copy()
    mean_scaling_df = mean_scaling_df[mean_scaling_df["Outcome"] == "O_" + dv]
    idvs = data_df.columns
    scaled_df = data_df.copy()

    for var in list(idvs):
        if var not in list(mean_scaling_df["Variable"]):
            continue

        scaling_factor = mean_scaling_df[mean_scaling_df["Variable"] == var][
            "mean"
        ].iloc[0]
        scaled_df[var] = scaled_df[var] / scaling_factor

    model_df = log_transformation(scaled_df.fillna(0), idvs)
    coefficient_df = coefficient_df[coefficient_df["outcome"] == "O_" + dv]
    preds = predict(model_df, idvs, coefficient_df)

    return preds

def sum_over_solution_idvs(sol_df, idvs):
    '''
            used for group constraint violation calculation
    '''
    total = sol_df[idvs].sum().sum()
    return total
