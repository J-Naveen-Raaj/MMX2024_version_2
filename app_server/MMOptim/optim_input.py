# -*- coding: utf-8 -*-
import os

import numpy as np
import pandas as pd

from app_server.MMOptim.utils.data_utils import get_array_position

# %% Function to get optimization input from excel


def get_optim_input(optim_input_dir, optim_input_file, spend_vars=None):
    """
    Get optimization input from excel file
    """
    ## Main Optim Input
    main_input = pd.read_excel(
        os.path.join(optim_input_dir, optim_input_file),
        sheet_name="Optim Input",
        index_col=0,
        header=None,
        # squeeze=True,
    )
    main_input = main_input[1]

    ## Base Scenario
    base_scenario = pd.read_excel(
        os.path.join(optim_input_dir, optim_input_file),
        sheet_name="Base Scenario",
        index_col=0,
    )
    if spend_vars is not None:
        base_scenario = base_scenario.loc[spend_vars, :]

    ## Variable Description
    var_desc_cols = ["Variable Category", "Variable Description"]
    var_desc = base_scenario[var_desc_cols]

    ## Individual Spend Bounds
    var_bounds = pd.read_excel(
        os.path.join(optim_input_dir, optim_input_file),
        sheet_name="Individual Bounds - Quarterly",
    )
    var_bounds.set_index(["Variable Name", "Time Period"], inplace=True)
    #    if spend_vars is not None:
    #        var_bounds = var_bounds.loc[spend_vars,:]
    # When individual variables are locked,
    # make % bounds equal to 0 and $ bounds equal to base scenario numbers
    cond = var_bounds["Lock"] == "Yes"
    if np.any(cond):
        var_bounds.loc[cond, ["Lower Bound", "Upper Bound"]] = var_bounds.loc[
            cond, "Base Scenario"
        ]

    ## Variable Group Definition - For Group Constraints
    var_group = pd.read_excel(
        os.path.join(optim_input_dir, optim_input_file),
        sheet_name="Variable Group Definition",
        index_col=0,
    )
    if spend_vars is not None:
        var_group = var_group.loc[spend_vars, :]

    ## Variable Group Constraints
    var_group_cons = pd.read_excel(
        os.path.join(optim_input_dir, optim_input_file), sheet_name="Group Constraints"
    )

    optim_input = {
        "main_input": main_input,
        "base_scenario": base_scenario,
        "var_desc": var_desc,
        "var_bounds": var_bounds,
        "var_group": var_group,
        "var_group_cons": var_group_cons,
    }
    return optim_input


# %% Function to process optimization input


# def process_optim_input(optim_input, spend_vars, period_list, refc_scenario):
def process_optim_input(optim_input, spend_vars, period_list):
    """
    Process optimization input to get base scenario, individual spend bounds and constraints.
    """
    ### Base Scenario (spends by period)
    base_scenario = optim_input["var_bounds"]["Base Scenario"].unstack(level=-1)
    flags_vars = list(filter(lambda val: "_FLAGS_" in val, spend_vars))
    flags_ser = pd.DataFrame(index=flags_vars, columns=period_list, dtype=np.int32)
    flags_ser.columns.name = "Period"
    flags_ser.index.name = "Variable Name"
    flags_ser.loc[flags_vars, period_list] = 0

    # base_scenario.loc[flags_vars, :] = 0
    base_scenario = pd.concat([base_scenario, flags_ser], axis=0)
    base_scenario = base_scenario.loc[spend_vars, period_list]
    base_scenario = base_scenario.loc[~base_scenario.index.duplicated(keep="last")]

    ### Individual Spend Variable Bounds (by period)

    lower_bounds = optim_input["var_bounds"]["Lower Bound"].unstack(level=-1)
    lower_bounds = pd.concat([lower_bounds, flags_ser], axis=0)
    lower_bounds = lower_bounds.loc[spend_vars, period_list]
    lower_bounds = lower_bounds.loc[~lower_bounds.index.duplicated(keep="last")]

    upper_bounds = optim_input["var_bounds"]["Upper Bound"].unstack(level=-1)
    upper_bounds = pd.concat([upper_bounds, flags_ser], axis=0)
    upper_bounds = upper_bounds.loc[spend_vars, period_list]
    upper_bounds = upper_bounds.loc[~upper_bounds.index.duplicated(keep="last")]

    ### Variable Group definition

    var_group = optim_input["var_group"]
    var_group_dict = {}
    for group_name in var_group.columns[2:]:
        var_list = var_group[var_group[group_name] == 1].index.tolist()
        if len(var_list):
            var_group_dict[group_name] = var_list

    ### Variable Group Constraints

    var_group_cons = optim_input["var_group_cons"].copy()
    period_conversion_dict = {
        "Overall": "Overall",
        "1": "Q1",
        "2": "Q2",
        "3": "Q3",
        "4": "Q4",
    }

    var_group_cons["Period"] = var_group_cons["Period"].map(period_conversion_dict)

    # Removing group constraints if some field is not defined
    var_group_cons.dropna(axis=0, inplace=True)
    # Removing group constraints if the group is not defined
    var_group_cons = var_group_cons.loc[
        var_group_cons["Variable Group"].isin(var_group_dict.keys()), :
    ]
    # Removing group constraints if period is out of optimization period range
    var_group_cons = var_group_cons.loc[
        var_group_cons["Period"].isin(["Overall"] + period_list), :
    ]

    constraints = {}
    for index, cons in var_group_cons.iterrows():
        group_name = cons["Variable Group"]
        var_list = var_group_dict[group_name]
        cons_period = cons["Period"]
        cons_type = cons["Constraint Type"]
        cons_value = cons["Value"]
        if len(var_list) == 1 and cons_period != "Overall":
            # single variable, single period constraints - update individual bounds
            if cons_type == "Lock":
                lower_bounds.loc[var_list[0], cons_period] = cons_value
                upper_bounds.loc[var_list[0], cons_period] = cons_value
            if cons_type == "Cap":
                upper_bounds.loc[var_list[0], cons_period] = cons_value
            if cons_type == "Min":
                lower_bounds.loc[var_list[0], cons_period] = cons_value
        else:
            # other constraints - either no. of variables > 1 or overall period or both
            # create constraints for each of them
            cons_key = (group_name, cons_period, cons_type)
            periods = [cons_period] if cons_period != "Overall" else period_list
            pos = get_array_position(
                base_scenario, select_index=var_list, select_columns=periods
            )
            constraints[cons_key] = {
                "var_list": var_list,
                "period_list": periods,
                "pos": pos,
                "type": cons_type,
                "value": cons_value,
            }

    ### Budget for Optimization - Base, Incremental and Total
    """
    Note: 'Total' is not always 'Base' + 'Incremental'.
    Only in case of Incremental budget optimization, 'Incremental' will be non-zero.
    Otherwise, 'Incremental' will be 0 and 'Total' will be either 'Base' or a new overall budget.
    """
    budget = {
        "base": optim_input["main_input"]["budget_base"],
        "incremental": optim_input["main_input"]["budget_incremental"],
        "total": optim_input["main_input"]["budget_total"],
    }

    return base_scenario, lower_bounds, upper_bounds, constraints, budget
