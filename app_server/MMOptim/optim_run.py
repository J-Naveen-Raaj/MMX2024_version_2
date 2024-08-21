# -*- coding: utf-8 -*-
import os
import time
from datetime import timedelta

import numpy as np
import pandas as pd

from app_server.custom_logger import get_logger
from app_server.MMOptim.config import (
    OPTIM_INPUT_DIR,
    OPTIM_LOG_DIR,
    OPTIM_OUTPUT_DIR,
    REFERENCE_CALENDAR_YEAR,
)

### Local Modules
from app_server.MMOptim.constants import DICT_OBJECTIVES, MONTHS, QUARTERS
from app_server.MMOptim.DE_core import Differential_Evolution

### Modules for Gradient Projection method
from app_server.MMOptim.gp_optim_problem import get_obj_func
from app_server.MMOptim.gp_optim_utils import get_init_sol, process_bounds
from app_server.MMOptim.NSGA_II_core import NSGA
from app_server.MMOptim.optim_input import get_optim_input, process_optim_input
from app_server.MMOptim.optim_output import get_optim_output, write_output_to_excel
from app_server.MMOptim.preprocessing import (
    filter_data,
    get_ref_calendar_outcome_totals,
)
from app_server.MMOptim.ratio_convertion import get_spend_totals_by_group
from app_server.MMOptim.static_input_optim import get_static_input
from app_server.MMOptim.utils.data_utils import add_subtotals
from app_server.MMOptim.utils.tee import Tee
from app_server.MMOptim.validation import (
    ValidationError,
    basic_validation,
    feasibility_check,
)
from app_server.what_if_planner_handler import what_if_planner

logger = get_logger(__name__)


# %% Run Optimization


def run_optimization(
    optim_input_file, optim_output_file=None, optim_input=None, **kwargs
):
    """
    Main function to run the optimization.

    Parameters
    ----------
    optim_input_file : str
        Filename for the optimization input without dir.
        Directory of this file should be specified in 'config.py' as OPTIM_INPUT_DIR.

    Returns
    -------
        This function doesn't return any value. It runs the optimization for
        the given input in optim_input_file and saves the output excel file
        in the directory specified as OPTIM_OUTPUT_DIR in 'config.py'.
    """
    print(
        "================================================================================"
    )
    print("Market Mix Optimization - Start |", time.ctime())
    print(
        "--------------------------------------------------------------------------------"
    )
    print("Optimization Input File:", optim_input_file)
    print(
        "--------------------------------------------------------------------------------"
    )

    start_time = time.time()
    print(kwargs["year"], " - Year time period")

    # print(optim_input)

    ### Static Input -------------------------------------------------------------------------------

    print("Getting static input ...")
    (
        all_data,
        spend_vars,
        spend_scaling_factor,
        coeffs_mktg,
        coeffs_mktg_simpl,
        var_map_df,
        calendar,
    ) = get_static_input(disp=True)

    ### Optimization Input -------------------------------------------------------------------------
    print("Getting optimization input ...")

    # Get optimization input
    if optim_input is None:
        optim_input = get_optim_input(
            OPTIM_INPUT_DIR, optim_input_file, spend_vars=None
        )

    ### Preprocessing ------------------------------------------------------------------------------

    print("Preprocessing ...")

    # Reference calendar
    # ref_calendar = calendar.loc[(calendar["YEAR"] == REFERENCE_CALENDAR_YEAR), :]
    period_year = optim_input["main_input"]["period_year"]
    ref_calendar = calendar.loc[(calendar["YEAR"] == period_year), :]
    # ref_calendar = calendar.loc[(calendar["YEAR"] == REFERENCE_CALENDAR_YEAR), :]
    # print(ref_calendar.shape)

    # week_counts_map = (
    #     ref_calendar.assign(quarter_name="Q" + ref_calendar["QUARTER"].astype(str))
    #     .groupby("quarter_name")["Week end Date"]
    #     .count()
    # )
    # var_bounds = optim_input["var_bounds"].reset_index()
    # print(var_bounds.columns)
    # var_bounds["week_count"] = var_bounds["Period"].map(week_counts_map)
    # var_bounds["Lower Bound"] = var_bounds["Lower Bound"] / var_bounds["week_count"]
    # var_bounds["Upper Bound"] = var_bounds["Upper Bound"] / var_bounds["week_count"]
    # var_bounds = pd.merge(
    #     var_bounds,
    #     ref_calendar.assign(quarter_name="Q" + ref_calendar["QUARTER"].astype(str)),
    #     left_on=["Period"],
    #     right_on=["quarter_name"],
    #     how="left",
    # )
    # var_bounds["Lower Bound"] = var_bounds["Lower Bound"].astype(int)
    # var_bounds = var_bounds.set_index(["Variable Name", "Period"])

    optim_input["var_bounds"]["Lower Bound"] = optim_input["var_bounds"][
        "Lower Bound"
    ].astype(int)

    # Period of Optimization
    period_type = optim_input["main_input"]["period_type"].upper()
    start_period, end_period = optim_input["main_input"][["period_start", "period_end"]]

    # Filter data for a given period of optimization
    data = filter_data(all_data, ref_calendar, period_type, start_period, end_period)

    # List of periods
    if period_type == "QUARTER":
        period_list = [QUARTERS[i] for i in range(start_period - 1, end_period)]
        period_group_cols = ["X_QTR"]
    elif period_type == "MONTH":
        period_list = [MONTHS[i] for i in range(start_period - 1, end_period)]
        period_group_cols = ["X_MONTH"]
    else:
        raise ValueError(
            "Unknown period_type '%s'; should be one of ['QUARTER', 'MONTH']"
            % period_type
        )
    print(all_data.columns)
    print(data.columns)
    print(all_data["X_DT"].unique())
    print(data["X_DT"].unique())
    print("period list", period_list)

    # refc_scenario = get_spend_totals_by_period(
    #     data, spend_vars, spend_scaling_factor, DATE_COL
    # )

    # Reference calendar spend scenario
    refc_scenario = get_spend_totals_by_group(
        data, spend_vars, spend_scaling_factor, period_group_cols
    )
    print(refc_scenario.columns)
    refc_scenario.columns = period_list

    # Reference calendar outcome vars total
    # outcome_totals_week = get_ref_calendar_outcome_totals_1(
    #     data, ref_calendar  # , time_var=period_type
    # )

    # Reference calendar outcome vars total
    outcome_totals = get_ref_calendar_outcome_totals(
        data, ref_calendar, time_var=period_type
    )
    outcome_totals.columns = period_list

    ### Process Optimization Input -----------------------------------------------------------------

    print("Processing optimization input ...")

    (
        base_scenario,
        lower_bounds,
        upper_bounds,
        constraints,
        budget,
    ) = process_optim_input(optim_input, spend_vars, period_list)
    # ) = process_optim_input(optim_input, spend_vars, period_list, refc_scenario)

    ### Validation
    print("print group constraints")
    print(constraints)
    ## Basic validation to check for level 1 errors and warnings
    try:
        logger.info("Starting basic validations")
        report = basic_validation(
            base_scenario, lower_bounds, upper_bounds, constraints, budget
        )
    except Exception as e:
        print("Basic validation failed !")
        logger.info("Basic validation failed !")
        raise ValidationError(e.args)
        return
    else:
        logger.info(report)
        print(report)

    ## Feasibility check
    logger.info("Starting the feasibility check")
    is_feasible = feasibility_check(
        base_scenario, lower_bounds, upper_bounds, constraints, budget
    )
    if not is_feasible:
        logger.info(
            "Given constraints infeasible, retry with new constraints and bounds"
        )
        print("Given constraints infeasible, retry with new constraints and bounds")
        return

    print("All constraints validated succesfully")

    # List of outcome - segment combinations for the objective to maximize
    print(optim_input["main_input"]["objective_to_max"])
    objective_to_max = optim_input["main_input"]["objective_to_max"]
    obj = DICT_OBJECTIVES[objective_to_max]
    obj_list = [(oc, seg) for oc, seg_list in obj.items() for seg in seg_list]
    print("*************************************************************")
    print(obj)

    # Get initial solution and constraints in form of A_ub, b_ub
    X_init, A_ub, b_ub, lb, ub, lock_cons_index = get_init_sol(
        lower_bounds, upper_bounds, budget, constraints, method="simplex"
    )
    # Get bounds in updated A_ub, b_ub for GP
    # A_ub * x = b_ub
    A_ub, b_ub, pos_locked, pos_unlocked, all_var_locked_cons = process_bounds(
        lb, ub, A_ub, b_ub, budget
    )
    # Remove group constraints from lock_cons_index where all variables are individually locked as well
    # lock_cons_index = np.delete(lock_cons_index, all_var_locked_cons)

    # Get objective function which gives initial slope and y_predicted for the given spend
    # obj_func = get_obj_func(
    #     obj_list, coeffs_mktg_simpl, outcome_totals, refc_scenario, X_init, pos_unlocked
    # )

    # slope, y_predicted = obj_func(X_init[pos_unlocked])

    bounds = list(zip(lb[pos_unlocked], ub[pos_unlocked]))

    # -------------------------------------------------------------

    base_budgets = list(base_scenario.sum() / base_scenario.sum().sum())
    ### Run Optimization ---------------------------------------------------------------------------
    if len(bounds):
        print("Starting optimization ...")
        logger.info("Starting optimization ...")

        optim_start_time = time.time()

        try:
            # x, result = gradient_projection(
            #     obj_func=obj_func,
            #     A_ub=A_ub,
            #     b_ub=b_ub,
            #     x=X_init[pos_unlocked],  # providing spends for only unlocked variables
            #     bounds=bounds,
            #     step_adj_param=1000000,
            #     maxiter=200,
            #     tol=-1e-3,
            #     lock_cons_index=lock_cons_index,
            #     y_best=y_predicted,
            # )

            if objective_to_max == "outcome1" or objective_to_max == "outcome2":
                x, result, convergence = Differential_Evolution(
                    budget=budget["total"],
                    lower_bounds=lower_bounds,
                    upper_bounds=upper_bounds,
                    dv=objective_to_max,
                    period_year=period_year,
                    period_type=period_type,
                    split_budget_proportion=base_budgets,
                    group_constraints=constraints,
                )

            else:
                print("multi-objective")
                x, result, convergence = NSGA(
                    budget=budget["total"],
                    lower_bounds=lower_bounds,
                    upper_bounds=upper_bounds,
                    period_year=period_year,
                    period_type=period_type,
                    split_budget_proportion=base_budgets,
                    group_constraints=constraints,
                )

        except Exception as e:
            print(e.args)
            logger.error(f"Error occurred in optimization algorithm {e}")
            raise ValidationError("Error occurred in optimization algorithm")

        optim_end_time = time.time()

        logger.info("Optimization run ended...")

        print(
            "Time taken for optimization: %s"
            % str(timedelta(seconds=(optim_end_time - optim_start_time)))
        )

        ### Optimization Output ------------------------------------------------------------------------

        print("Getting optimization output ...")

        # Rounding off the decimal part

        lower_bounds = lower_bounds.round(decimals=0)
        upper_bounds = upper_bounds.round(decimals=0)

        pos_unlocked = np.where(lower_bounds != upper_bounds)

        optimal_solution = x[pos_unlocked]
        optimal_scenario = upper_bounds.copy()

        optimal_scenario.values[pos_unlocked] = optimal_solution
    else:
        optimal_scenario = base_scenario

    if kwargs["base_outcome_split"] is not None:
        base_scenario_outcome = pd.DataFrame(kwargs["base_outcome_split"])

    base_scenario_input = optim_input["base_scenario"]
    # fill optimal scenarios with 0 spends for periods except from start to end
    if period_type == "QUARTER":
        optimal_scenario = optimal_scenario.rename(
            columns={f"Q{idx+1}": idx + 1 for idx in range(4)}
        ).rename(columns={f"Q_{idx+1}": idx + 1 for idx in range(4)})
        base_scenario_input = base_scenario_input.rename(
            columns={f"Q{idx+1}": idx + 1 for idx in range(4)}
        ).rename(columns={f"Q_{idx+1}": idx + 1 for idx in range(4)})
    elif period_type == "MONTH":
        optimal_scenario = (
            optimal_scenario.rename(
                columns={mon: (idx + 1) for idx, mon in enumerate(MONTHS)}
            )
            .rename(columns={f"M{idx+1}": idx + 1 for idx in range(12)})
            .rename(columns={f"M_{idx+1}": idx + 1 for idx in range(12)})
        )
        base_scenario = (
            base_scenario.rename(
                columns={mon: (idx + 1) for idx, mon in enumerate(MONTHS)}
            )
            .rename(columns={f"M{idx+1}": idx + 1 for idx in range(12)})
            .rename(columns={f"M_{idx+1}": idx + 1 for idx in range(12)})
        )
        base_scenario_input = (
            base_scenario_input.rename(
                columns={mon: (idx + 1) for idx, mon in enumerate(MONTHS)}
            )
            .rename(columns={f"M{idx+1}": idx + 1 for idx in range(12)})
            .rename(columns={f"M_{idx+1}": idx + 1 for idx in range(12)})
        )

    start_period, end_period = (
        optimal_scenario.columns.min(),
        optimal_scenario.columns.max(),
    )
    start_period, end_period = int(start_period), int(end_period)
    period_type_end_mapping = {"MONTH": 12, "QUARTER": 4}
    period_type_end = period_type_end_mapping.get(period_type, 12)

    for period in range(1, start_period):
        if period in base_scenario_input.columns:
            optimal_scenario[period] = base_scenario_input[period]
        else:
            print(f"{period} missing in base scenario, filling with 0")
            optimal_scenario[period] = 0
    for period in range(end_period, period_type_end):
        if period in base_scenario_input.columns:
            optimal_scenario[period + 1] = base_scenario_input[period + 1]
        else:
            print(f"{period+1} missing in base scenario, filling with 0")
            optimal_scenario[period + 1] = 0

    optimal_spend = (
        optimal_scenario.unstack()
        .rename("spend_value")
        .reset_index()
        .rename(
            columns={
                "Period": "period_name",
                "Variable Name": "node_name",
            }
        )
    )

    monthly_base_scenario = optim_input.get("monthly_base_scenario")
    if monthly_base_scenario is not None:
        monthly_base_scenario["QUARTER"] = monthly_base_scenario["MONTH"].map(
            lambda val: (val - 1) // 3 + 1
        )
        monthly_base_scenario = monthly_base_scenario.rename(
            columns={"Variable Name": "node_name"}
        )
        monthly_base_scenario["spend_value"] = (
            monthly_base_scenario["spend_value"].fillna(0) + 1
        )
        monthly_base_scenario["ratio"] = monthly_base_scenario["spend_value"].div(
            monthly_base_scenario.groupby(["node_name", period_type])[
                "spend_value"
            ].transform(sum)
        )
        monthly_base_scenario = monthly_base_scenario.loc[
            :, ["node_name", "QUARTER", "MONTH", "ratio"]
        ]
        optimal_monthly_spend = pd.merge(
            optimal_spend,
            monthly_base_scenario,
            left_on=["node_name", "period_name"],
            right_on=["node_name", period_type],
            how="inner",
        )
        optimal_monthly_spend["distributed_spend_value"] = (
            optimal_monthly_spend["spend_value"] * optimal_monthly_spend["ratio"]
        )
        optimal_scenario = pd.pivot_table(
            data=optimal_monthly_spend.rename(
                columns={"node_name": "Variable Name", "QUARTER": "Period"}
            ),
            index=["Variable Name"],
            columns="Period",
            values=["spend_value"],
            aggfunc=sum,
        ).droplevel(axis=1, level=0)

        optimal_spend = optimal_monthly_spend.loc[
            :, ["node_name", "MONTH", "distributed_spend_value"]
        ]
        optimal_spend = optimal_spend.rename(
            columns={"distributed_spend_value": "spend_value", "MONTH": "period_name"}
        )
        optimal_spend["spend_value"] = optimal_spend["spend_value"].fillna(0)
        period_type = "MONTH"

    prefixes = {"QUARTER": "Q", "MONTH": "M"}
    period_type_end = period_type_end_mapping.get(period_type, 12)
    optimal_spend["period_name"] = optimal_spend["period_name"].replace(
        {idx + 1: f"{prefixes[period_type]}{idx+1}" for idx in range(period_type_end)}
    )

    if period_type == "MONTH":
        optimal_scenario = (
            optimal_scenario.rename(
                columns={(idx + 1): mon for idx, mon in enumerate(MONTHS)}
            )
            .rename(columns={f"M{(idx + 1)}": mon for idx, mon in enumerate(MONTHS)})
            .rename(columns={f"M_{(idx + 1)}": mon for idx, mon in enumerate(MONTHS)})
        )

    elif period_type == "QUARTER":
        optimal_scenario = optimal_scenario.rename(
            columns={(idx + 1): f"Q{idx+1}" for idx in range(4)}
        )
    # change num to name in optimal_scenario

    optimal_spend["geo"] = "US"
    optimal_spend["period_type"] = period_type.lower() + "ly"

    # base_spend = (
    #     base_scenario.unstack()
    #     .rename("spend_value")
    #     .reset_index()
    #     .rename(columns={"Period": "period_name", "Variable Name": "node_name"})
    # )
    # if period_type == "QUARTER":
    #     base_spend["period_name"] = (
    #         base_spend["period_name"].str.replace("Q", "").astype("int64")
    #     )
    # elif period_type == "MONTH":
    #     base_spend["period_name"] = (
    #         base_spend["period_name"]
    #         .map({mon: (idx + 1) for idx, mon in enumerate(MONTHS)})
    #         .astype("int64")
    #     )

    # base_spend["geo"] = "US"
    # base_spend["period_type"] = period_type.lower() + "ly"

    logger.info("Running what if for optimized spend")

    final_output, optimization_scenario_outcome = what_if_planner(
        optimal_spend, period_type.lower() + "ly", kwargs["year"]
    )
    logger.info("What if completed for optimized spend")

    optimization_scenario_outcome.rename(
        columns={"Outcome": "outcome", "Segment": "segment"}, inplace=True
    )
    base_scenario_outcome.rename(
        columns={
            "Outcome": "outcome",
            "Segment": "segment",
            "baseattribution": "BaseAttribution",
            "marketingattribution": "MarketingAttribution",
            "externalattribution": "ExternalAttribution",
        },
        inplace=True,
    )
    base_scenario_base_contrib = base_scenario_outcome.set_index(
        ["outcome", "segment"]
    )["BaseAttribution"]

    optim_scenario_base_contrib = optimization_scenario_outcome.set_index(
        ["outcome", "segment"]
    )["BaseAttribution"]

    base_scenario_outcome_total = (
        base_scenario_outcome.set_index(["outcome", "segment"])["MarketingAttribution"]
        + base_scenario_outcome.set_index(["outcome", "segment"])["BaseAttribution"]
        + base_scenario_outcome.set_index(["outcome", "segment"])["ExternalAttribution"]
    )

    optim_scenario_outcome_total = (
        optimization_scenario_outcome.set_index(["outcome", "segment"])[
            "MarketingAttribution"
        ]
        + optimization_scenario_outcome.set_index(["outcome", "segment"])[
            "BaseAttribution"
        ]
        + optimization_scenario_outcome.set_index(["outcome", "segment"])[
            "ExternalAttribution"
        ]
    )

    optim_output = get_optim_output(
        base_scenario,
        optimal_scenario,
        optim_input,
        lower_bounds,
        upper_bounds,
        obj_list,
        period_list,
        period_group_cols,
        coeffs_mktg,
        var_map_df,
        base_scenario_base_contrib,
        optim_scenario_base_contrib,
        base_scenario_outcome_total,
        optim_scenario_outcome_total,
        convergence=convergence,
    )
    print("Final Output-----------------------------------")
    print(final_output)
    optim_output["final_output"] = final_output
    optim_output["optimization_scenario_outcome"] = optimization_scenario_outcome

    print("\n")
    print("Overall comparison :::")
    print(optim_output["overall"])

    print("\n")
    print("Outcome comparison :::")
    print(optim_output["outcome"].xs("Total", axis=1, level=1))

    print("\n")
    print("Writing optimization output to excel ...")
    write_output_to_excel(
        optim_output,
        OPTIM_OUTPUT_DIR,
        optim_output_file,
        objective_to_max,
        len(period_list),
    )
    print("Optimization output saved in file:", optim_output_file)

    end_time = time.time()
    print("Overall time taken: %s" % str(timedelta(seconds=(end_time - start_time))))

    print(
        "--------------------------------------------------------------------------------"
    )
    print("Market Mix Optimization - End |", time.ctime())
    print(
        "--------------------------------------------------------------------------------"
    )

    return optim_output


def run_optimization_with_UI(optim_input, filename, **kwargs):
    optim_input_file = os.path.join(
        # "app_server",
        "Tiger MMX - Optimization input.xlsx"
    )
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = optim_input_file.replace(".xlsx", "_log_" + timestamp + ".txt")
    optim_output_file = filename + ".xlsx"
    optim_output = run_optimization(
        optim_input_file, optim_output_file, optim_input, **kwargs
    )
    convergence = optim_output["convergence"]
    optimal_spend_plan = optim_output.get("optimal_spend_plan")
    final_output = optim_output.get("final_output")
    optimization_scenario_outcome = optim_output.get("optimization_scenario_outcome")
    return (
        convergence,
        optim_output_file,
        log_file,
        optimal_spend_plan,
        final_output,
        optimization_scenario_outcome,
    )
