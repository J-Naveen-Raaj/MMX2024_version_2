# -*- coding: utf-8 -*-
import os

import numpy as np
import pandas as pd

from app_server.database_handler import DatabaseHandler
from app_server.MMOptim.constants import (ALL_GEOS, ALL_SEGS, DATE_COL,
                                          GEO_COL, MONTHS, QUARTERS, SEG_COL)
from app_server.MMOptim.utils.misc import match_pos
from app_server.MMOptim.utils.str_utils import (str_contains, str_endswith,
                                                str_startswith)
from app_server.scenario_dao import ScenarioDAO

# %% Load Data
db_conn = DatabaseHandler().get_database_conn()
scenario_dao = ScenarioDAO(db_conn)


def load_data(data_file):
    """
    Load Data
    """
    # data = pd.read_csv(data_file)

    data = data_file
    # Parse date column
    data[DATE_COL] = pd.to_datetime(data[DATE_COL], format="%Y-%m-%d")
    # data[DATE_COL] = pd.to_datetime(data[DATE_COL], format="ISO8601")

    # Sort data by Segment - Geo - Date
    sort_cols = [SEG_COL, GEO_COL, DATE_COL]
    data.sort_values(by=sort_cols, inplace=True)

    return data



# %% Transform Data


def transform_data_what_if(data):
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
    promo_cols = str_startswith(all_cols, "E_")
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


