# -*- coding: utf-8 -*-

import os

import numpy as np
import pandas as pd

from app_server.database_handler import DatabaseHandler
from app_server.MMOptim.constants import (
    ALL_GEOS,
    ALL_SEGS,
    DATE_COL,
    GEO_COL,
    MONTHS,
    QUARTERS,
    SEG_COL,
)
from app_server.MMOptim.utils.misc import match_pos
from app_server.MMOptim.utils.str_utils import (
    str_contains,
    str_endswith,
    str_startswith,
)
from app_server.scenario_dao import ScenarioDAO

WEEK_END_DATE_COL = "Week end Date"

# %% Load Data
db_conn = DatabaseHandler().get_database_conn()
scenario_dao = ScenarioDAO(db_conn)


def load_data(data_file):
    """
    Load Data
    """
    data = data_file

    # Parse date column
    data[DATE_COL] = pd.to_datetime(
        # data[DATE_COL], infer_datetime_format=True, format="%Y-%m-%d"
        data[DATE_COL],
        infer_datetime_format=True,
        format="%Y-%m-%d",
    )

    # Sort data by Segment - Geo - Date
    sort_cols = [SEG_COL, GEO_COL, DATE_COL]
    data.sort_values(by=sort_cols, inplace=True)

    return data


# %% Transform Data


def transform_data(data):
    """
    Transform Data - create new columns or modify existing columns
    """
    # Months and Quarters - convert to numeric
    try:
        data["X_MONTH"] = (
            np.array(match_pos(data["X_MONTH"], MONTHS)) + 1
        )  # Add 1 since pos is 0-indexed
    except ValueError:
        print("X_MONTH in numerics already")
    try:
        data["X_QTR"] = (
            np.array(match_pos(data["X_QTR"], QUARTERS)) + 1
        )  # Add 1 since pos is 0-indexed
    except ValueError:
        print("X_QTR in numerics already")

    # Half Year
    data["X_HY"] = np.ceil(data["X_QTR"] / 2)

    # Negative to positive correlation variable for variables present in model
    # vars_neg_corr = ["CP_M_VG_SP", "CP_M_EJ_SP", "CP_M_ET_SP", "CP_M_TD_SP", "CP_M_BM_SP", "CP_M_JP_SP", "CP_M_MS_SP",
    #                  "CP_M_RH_SP", "CP_M_FD_SP", "CP_M_ML_SP", "EC_UNEMP"]
    # data[vars_neg_corr] = data[vars_neg_corr].apply(lambda x: 1/x)

    return data


# %% Get Data Columns


def get_data_columns(all_cols, lag_vars):
    """
    Identify Different Columns of Data
    """
    # ID Columns
    id_cols = str_startswith(all_cols, "X_")

    # Media Columns
    media_cols = str_startswith(all_cols, "M_") + lag_vars

    # Promotion Columns
    promo_cols = str_startswith(all_cols, "PRO_")
    for col in str_contains(promo_cols, "_TRD_"):
        promo_cols.remove(col)

    # Marketing Columns
    mktg_cols = media_cols + promo_cols

    # Marketing Spend Columns
    mktg_sp_cols = str_endswith(mktg_cols, "_SP")

    return id_cols, media_cols, promo_cols, mktg_cols, mktg_sp_cols


# %% Spend Variable Mapping


def get_spend_var_mapping(mktg_cols, spend_vars=None, spend_var_suffix="_SP"):
    """
    Get Spend variable mapping for a given list of Marketing Variables

    Parameters
    ----------
    mktg_cols : array-like or list
        List of marketing columns in the data.

    spend_vars : array-like or list, optional
        List of spend variables.

    spend_var_suffix: str
        Suffix of the spend variables in the data. Default is '_SP'.

    Returns
    -------
    variable_mapping : pandas.DataFrame
        A DataFrame containing two columns 'Variable', 'Spend_Variable'.
        The first column having the marketing variables/columns in the data
        with corresponding spend variable in the second column.
    """
    if spend_vars is not None:
        mktg_sp_cols = spend_vars.copy()
    else:
        mktg_sp_cols = str_endswith(mktg_cols, spend_var_suffix)
    vm_df = pd.DataFrame(columns=["Variable", "Spend_Variable"])
    for sp_var in mktg_sp_cols:  # for each spend variable
        tmp_df = pd.DataFrame()
        tmp_df["Variable"] = str_startswith(mktg_cols, sp_var[: -len(spend_var_suffix)])
        tmp_df["Spend_Variable"] = sp_var
        # vm_df = vm_df.append(tmp_df, ignore_index=True)
        vm_df = pd.concat([tmp_df, vm_df])
    vm_df["temp"] = vm_df["Spend_Variable"].str.len()
    vm_df = vm_df.groupby("Variable").apply(lambda x: x[x["temp"] == x["temp"].max()])
    vm_df.drop(["temp"], axis=1, inplace=True)
    vm_df.reset_index(drop=True, inplace=True)
    return vm_df



def filter_coeffs(coeffs, select_vars):
    """
    Filter coefficients for only selected variables
    """
    coeffs_new = {}
    coeffs_new = coeffs.loc[coeffs.variable.isin(select_vars)].reset_index(drop=True)
    return coeffs_new


def reindex_coeffs(coeffs, variable_mapping):
    """
    Reindex coefficients with spend variable names
    """
    map_var2sp = dict(
        zip(variable_mapping["Variable"], variable_mapping["Spend_Variable"])
    )
    coeffs_new = coeffs.copy()
    coeffs_new = coeffs_new.set_index("variable")
    coeffs_new = coeffs_new.rename(index=map_var2sp, inplace=False)
    return coeffs_new


def simplify_coeffs(coeffs, all_vars=None):
    """
    Simplify coefficients by merging them into a single DataFrame
    """
    coeffs_simpl = pd.pivot_table(
        coeffs, index=["variable"], columns=["outcome", "X_SEG"]
    )
    coeffs_simpl.fillna(0, inplace=True)
    if all_vars:
        missing_vars = list(set(all_vars) - set(coeffs_simpl.index))
        coeffs_missing = pd.DataFrame(
            0, columns=coeffs_simpl.columns, index=missing_vars
        )
        # coeffs_simpl = coeffs_simpl.append(coeffs_missing).loc[all_vars,]
        coeffs_simpl = pd.concat([coeffs_simpl, coeffs_missing]).loc[all_vars,]
    # Dropping a level from multiindex
    coeffs_simpl.columns = coeffs_simpl.columns.droplevel(0)
    return coeffs_simpl


def retro_dictify(frame):
    """
    Convert the dataframe of coefficients into a nested dictionary
    """
    seq = ["outcome", "X_SEG", "variable", "X_GEO", "value"]
    d = {}
    for row in frame.values:
        here = d
        for elem in row[:-2]:
            if elem not in here:
                here[elem] = {}
            here = here[elem]
        here[row[-2]] = row[-1]
    for key, value in d.items():
        for key_1, value_1 in d[key].items():
            d[key][key_1] = pd.DataFrame(
                list(value_1.items()), columns=["variable", "Coefficient"]
            )
            d[key][key_1] = d[key][key_1].set_index("variable")
    return d


# %% Get All Static Input


def get_static_input(disp=True):
    """
    Get all static input

    Parameters
    ----------
    input_dir : str
         Input Directory; path for all input files.

    file_names : dict
        Dictionary containing file paths under the `input_dir`.
    """
    # Load & Transform Data
    if disp:
        print("Loading & transforming data ...")
    # data_file = os.path.join(input_dir, file_names["data_file"])
    data_file = pd.DataFrame.from_records(scenario_dao.get_forecastdata())
    data_file.columns = data_file.columns.str.upper()
    # data_file = pd.read_csv("app_server/MMO Data-20231027T071727Z-001/MMO Data/data/master_data.csv")
    all_data = load_data(data_file)
    all_data = transform_data(all_data)

    # Variable Levels
    if disp:
        print("Loading variable levels ...")
    # variable_levels_file = os.path.join(input_dir, file_names["variable_levels_file"])
    # variable_levels = pd.read_csv(variable_levels_file)
    variable_levels = pd.DataFrame.from_records(scenario_dao.get_spendvariables())
    variable_levels = variable_levels.rename(
        columns={
            "Spend_Variable": "Spend Variable",
            "Variable_Category": "Variable Category",
            "Variable_Description": "Variable Description",
        },
    )

    # Spend Variables
    spend_vars = variable_levels["Spend Variable"].tolist()

    # if some spend variable is missing from data, add those variables to the data as 0
    missing_vars = [v for v in spend_vars if v not in all_data.columns]
    if missing_vars:
        print(
            "Warning: Missing variables from data: %s. Adding them to data as 0."
            % missing_vars
        )
        for v in missing_vars:
            all_data[v] = 0

    # Compute Spend Scaling Factor
    spend_scaling_factor = len(ALL_SEGS) ** (1 - variable_levels["Vary_by_SEG"]) * len(
        ALL_GEOS
    ) ** (1 - variable_levels["Vary_by_GEO"])
    spend_scaling_factor = pd.Series(spend_scaling_factor.values, index=spend_vars)

    # Identify Different Columns of Data
    id_cols, media_cols, promo_cols, mktg_cols, mktg_sp_cols = get_data_columns(
        all_data.columns, lag_vars=[]
    )

    # Coefficients
    if disp:
        print("Loading coefficients ...")
    seq = ["outcome", "X_SEG", "variable", "value"]
    coeffs = pd.DataFrame.from_dict(scenario_dao.get_model_coeff())
    coeffs = coeffs.rename(columns={"x_geo": "X_GEO", "x_seg": "X_SEG"})
    coeffs = coeffs.loc[:, seq]
    # coeff_file = os.path.join(input_dir, file_names["coeff_file_optim"])
    # coeffs = load_coeffs(coeff_file)

    coeffs_mktg = filter_coeffs(coeffs, mktg_cols)

    # List of variables being used in the models
    all_model_vars = list(coeffs_mktg.variable.unique())
    # Converting to a dictionary
    coeffs_mktg_dict = retro_dictify(coeffs_mktg)

    all_model_vars = sorted(list(set(all_model_vars + spend_vars)))

    # Marketing Spend Variable Mapping
    if disp:
        print("Getting variable mapping ...")
    # variable_mapping = get_spend_var_mapping(mktg_cols, spend_vars)
    var_map_df = get_spend_var_mapping(all_model_vars, spend_vars)

    # Marketing coefficients - simplified in a single DataFrame
    coeffs_mktg_simpl = simplify_coeffs(
        reindex_coeffs(coeffs_mktg, var_map_df), all_vars=spend_vars
    )

    # Calendar
    if disp:
        print("Loading calendar ...")
    # calendar_file = os.path.join(input_dir, file_names["calendar_file"])
    # calendar = pd.read_csv(calendar_file)
    calendardata = scenario_dao.get_calendar()
    calendar = pd.DataFrame.from_records(calendardata)
    calendar.rename(
        columns={
            "Week_end_Date": WEEK_END_DATE_COL,
            "month": "MONTH",
            "year": "YEAR",
            "quarter": "QUARTER",
        },
        inplace=True,
    )
    calendar[WEEK_END_DATE_COL] = pd.to_datetime(
        calendar[WEEK_END_DATE_COL],
        infer_datetime_format=True,
        format="%d-%m-%Y",
    )

    return (
        all_data,
        spend_vars,
        spend_scaling_factor,
        coeffs_mktg_dict,
        coeffs_mktg_simpl,
        var_map_df,
        calendar,
    )
