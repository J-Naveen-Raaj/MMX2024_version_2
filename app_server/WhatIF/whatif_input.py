# -*- coding: utf-8 -*-

import pandas as pd

from app_server.database_handler import DatabaseHandler
from app_server.MMOptim.constants import (
    ALL_SEGS,
    DATE_COL,
    GEO_COL,
    OUTCOME_VARS,
    SEG_COL,
)
from app_server.MMOptim.static_input import (
    get_data_columns,
    get_spend_var_mapping,
    load_data,
    transform_data_what_if,
)
from app_server.scenario_dao import ScenarioDAO

SPEND_VARIABLE_COL = "Spend Variable"
WEEK_END_DATE_COL = "Week end Date"

# %% Load Data
db_conn = DatabaseHandler().get_database_conn()
scenario_dao = ScenarioDAO(db_conn)


def get_input_data():
    """
    This function reads all the required files to run the whatif simulation
    and returns them in suitable format to runner code

    Returns:
        main_data -- Transformed Master Data
        id_cols -- List of ID columns (X_YEAR, X_MONTH ...)
        media_cols -- List of Media columns
        mktg_cols -- List of all marketing columns
        mktg_sp_cols -- List of Marketing columns refering to spends only
        spend_tp_mapping -- Spend Touchpoint Mapping DF
        var_type_dict -- Dictionary to differentiate between marketing and control vars
        dependent_variables -- List of DVs
        segments -- List of Segments
        model_coeffs -- A nested dictionary containing coefficients for all model variables by Outcome : Segment
        ratio_table
        adstock_variables
        calendar

    """
    # Load and transform Master Data
    forecast_data = scenario_dao.get_forecastdata()
    data_file = pd.DataFrame.from_records(forecast_data)
    data_file.columns = data_file.columns.str.upper()
    # data_file = pd.read_csv(
    #     "app_server/MMO Data-20231027T071727Z-001/MMO Data/data/master_data-v3.csv"
    # )
    main_data = load_data(data_file)
    main_data = transform_data_what_if(main_data.copy())

    # Get a dictionary mapping a variable to the type
    data_dictionary = scenario_dao.get_datadictonary()
    variable_type = pd.DataFrame.from_records(data_dictionary)
    # variable_type = pd.read_csv("app_server/MMO Data-20231027T071727Z-001/MMO Data/Files updated/Data Dictionary.csv")
    var_type_dict = {}
    for index, row in variable_type.iterrows():
        # var_type_dict.setdefault(row["Group"], []).append(row["Variable"])
        var_type_dict.setdefault(row["Group"], []).append(row["Spend_Variables"])

    # Get different types of variable
    lag_vars = [var for var in var_type_dict["Touchpoint"] if "_lag_" in var]
    id_cols, media_cols, promo_cols, mktg_cols, mktg_sp_cols = get_data_columns(
        main_data.columns, lag_vars
    )
    distribution_ratios_df = prepare_distribution_ratios(main_data, mktg_sp_cols)

    # Get spend touchpoint mapping
    spend_tp_mapping = get_spend_var_mapping(mktg_cols)

    # Get list of Dependent Variables and Segments
    dependent_variables = OUTCOME_VARS
    segments = ALL_SEGS

    # Get a dictionary of model coefficients for each Outcome X Segment
    model_coeff = scenario_dao.get_model_coeff()
    model_coeffs = pd.DataFrame.from_records(model_coeff)
    model_coeffs = model_coeffs.rename(columns={"x_geo": "X_GEO", "x_seg": "X_SEG"})
    # model_coeffs = pd.read_csv("app_server/MMO Data-20231027T071727Z-001/MMO Data/Files updated/model coefficients merged.csv")

    # Get ratio table for Geo X Segment split of marketing data
    year_ratio = scenario_dao.get_year_ratio()
    ratio_table = pd.DataFrame.from_records(year_ratio)
    ratio_table = ratio_table.rename(
        columns={"x_year": "X_YEAR", "x_geo": "X_GEO", "x_seg": "X_SEG"}
    )
    # ratio_table = pd.read_csv(
    #     "app_server/MMO Data-20231027T071727Z-001/MMO Data/year_ratios.csv"
    # )

    # Get data for ad_stock creation
    adstock_variables_ex = scenario_dao.get_ad_stocks_what_if_SU()
    adstock_variables_EX = pd.DataFrame.from_records(adstock_variables_ex)
    rename_map = {
        "ad_stock_variable": "Output Variable",
        "original_variable": "Original Variable",
        "ad_stock_half_life": "Ad-stock Half Life",
    }
    adstock_variables_EX.rename(columns=rename_map, inplace=True)
    adstock_variables_ntf = scenario_dao.get_ad_stocks_what_if_FTB()
    adstock_variables_NTF = pd.DataFrame.from_records(adstock_variables_ntf)
    # adstock_variables_NTF.rename(columns = {'ad_stock_variable':'Ad-stock Variable','original_variable' : 'Original Variable', 'ad_stock_half_life' : 'Ad-stock Half Life'}, inplace = True)
    # adstock_variables_NTF = pd.read_csv("app_server/MMO Data-20231027T071727Z-001/MMO Data/adstock_variable_what_if_FTBS.csv")
    adstock_variables_NTF.rename(columns=rename_map, inplace=True)

    # Get inflation factor for different media channels
    media_inflation = scenario_dao.get_media_inflation()
    media_inflation_data = pd.DataFrame.from_records(media_inflation)
    # media_inflation_data = pd.read_csv("app_server/MMO Data-20231027T071727Z-001/MMO Data/Files updated/Media_inflation_file.csv")

    # Get a dictionary of scaling files
    # min_max_dict = {}
    min_max = scenario_dao.get_min_max()
    min_max_df = pd.DataFrame.from_records(min_max)
    # for key in STATIC_FILENAMES["min_max_data"].keys():
    #     min_max_dict[key] = min_max_df.loc[min_max_df["Outcome"] == key]
    min_max_dict = {
        key: min_max_df.loc[min_max_df["Outcome"] == key]
        for key in {"outcome1", "outcome2"}
    }
    # Get list of spend variables
    # spend_variables = pd.read_csv("app_server/MMO Data-20231027T071727Z-001/MMO Data/spendvariables.csv")
    variablelevel_file = scenario_dao.get_spendvariables()
    spend_variables = pd.DataFrame.from_records(variablelevel_file)
    spend_variables.rename(
        columns={
            "Spend_Variable": SPEND_VARIABLE_COL,
            "Variable_Category": "Variable Category",
            "Variable_Description": "Variable Description",
        },
        inplace=True,
    )

    seasonality_data = scenario_dao.get_seasonality_data()
    seasonality = pd.DataFrame.from_records(seasonality_data)
    # seasonality = pd.read_csv("app_server/MMO Data-20231027T071727Z-001/MMO Data/seasonality.csv")

    # Get list of control mapping variables
    controlmapping = scenario_dao.get_controlmapping()
    control_mapping = pd.DataFrame.from_records(controlmapping)
    # control_mapping = pd.read_csv("app_server/MMO Data-20231027T071727Z-001/MMO Data/Files updated/Control_Mapping.csv")
    # Calendar for date to year - quarter - month - week mapping
    # calendar = pd.read_csv("app_server/MMO Data-20231027T071727Z-001/MMO Data/calendar-v1.csv")
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
        # format="%d-%m-%Y",
        format="%d-%m-%Y",
    )

    return (
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
    )


def prepare_distribution_ratios(
    master_data,
    mktg_cols,
):
    res = pd.melt(
        master_data,
        id_vars=[DATE_COL, GEO_COL, SEG_COL],
        value_vars=mktg_cols,
        var_name="node_name",
        value_name="SPENDS",
    )
    res["YEAR"] = res[DATE_COL].dt.year
    res["QUARTER"] = res[DATE_COL].dt.quarter
    res["MONTH"] = res[DATE_COL].dt.month
    res["WEEK"] = res[DATE_COL]
    return res


def get_variable_levels():
    """
    This function is used to return the variable levels file, later used to identify variables how vary by geo and segment
    """

    variablelevel_file = scenario_dao.get_spendvariables()
    variable_levels = pd.DataFrame.from_records(variablelevel_file)
    variable_levels.rename(
        columns={
            "Spend_Variable": SPEND_VARIABLE_COL,
            "Variable_Category": "Variable Category",
            "Variable_Description": "Variable Description",
        },
        inplace=True,
    )

    variable_levels.set_index(SPEND_VARIABLE_COL, inplace=True)

    variable_levels["multiplier"] = (25 ** (1 - variable_levels["Vary_by_GEO"])) * (
        3 ** (1 - variable_levels["Vary_by_SEG"])
    )

    return variable_levels
