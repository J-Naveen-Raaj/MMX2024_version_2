# -*- coding: utf-8 -*-
import os
import time

import numpy as np
import pandas as pd

# %% Compare Base vs New Scenario


def compare_base_vs_new(base, new, pct_scale=1):
    if pct_scale not in [1, 100]:
        raise ValueError(
            "Unknown value for 'pct_scale'. It can take value either 1 or 100."
        )
    comparison_table = pd.concat([base, new], axis=1)
    comparison_table["Change"] = new - base
    comparison_table["Change (%)"] = (new / base - 1) * pct_scale
    return comparison_table


# %% Get optimization output


def get_optim_output(
    base_scenario,
    optimal_scenario,
    optim_input,
    lower_bounds,
    upper_bounds,
    obj_list,
    period_list,
    group_cols,
    coeffs_mktg,
    var_map_df,
    base_scenario_base_contrib,
    optim_scenario_base_contrib,
    base_scenario_outcome_total,
    optim_scenario_outcome_total,
    pct_scale=1,
    convergence=True,
):
    """
    Get optimization output tables

    Parameters
    ----------
    pct_scale : numeric input
        Factor to use for scaling percentage numbers; can take value either 1 or 100, default 1.
        `pct_scale` 1 means 100% will be stored as 1 whereas 100 means 100% will be stored as 100.
    """

    ### Spend comparison

    var_desc = optim_input["var_desc"]
    spend_comparison = compare_base_vs_new(
        base_scenario.sum(axis=1).rename("Base Scenario"),
        optimal_scenario.sum(axis=1).rename("Optimal Scenario"),
        pct_scale,
    )
    spend_comparison = pd.merge(
        var_desc, spend_comparison, left_index=True, right_index=True
    )
    spend_comparison.reset_index(inplace=True)
    spend_comparison.sort_values(["Variable Description"], axis=0, inplace=True)

    optimal_spend_plan = pd.merge(
        var_desc, optimal_scenario, left_index=True, right_index=True
    )
    optimal_spend_plan.drop("Variable Category", axis=1, inplace=True)
    optimal_spend_plan.reset_index(inplace=True)
    optimal_spend_plan.sort_values(["Variable Description"], axis=0, inplace=True)

    # Spend by period in long format
    lb_long = (
        lower_bounds.rename_axis("Time Period", axis=1).stack().rename("Lower Bound")
    )
    ub_long = (
        upper_bounds.rename_axis("Time Period", axis=1).stack().rename("Upper Bound")
    )
    base_scn_long = (
        base_scenario.rename_axis("Time Period", axis=1).stack().rename("Base Scenario")
    )
    optim_scn_long = (
        optimal_scenario.rename_axis("Time Period", axis=1)
        .stack()
        .rename("Optimal Scenario")
    )
    spend_by_period = compare_base_vs_new(base_scn_long, optim_scn_long, pct_scale)
    spend_by_period = pd.concat([lb_long, ub_long, spend_by_period], axis=1)
    spend_by_period = spend_by_period.reset_index().set_index(["Variable Name"])
    spend_by_period = pd.merge(
        var_desc, spend_by_period, left_index=True, right_index=True
    )
    spend_by_period.reset_index(inplace=True)
    spend_by_period.sort_values(
        ["Variable Description", "Time Period"], axis=0, inplace=True
    )

    ### Outcome comparison

    base_scenario_outcome = pd.concat(
        {
            "Base": base_scenario_base_contrib,
            "Marketing": base_scenario_outcome_total - base_scenario_base_contrib,
            "Total": base_scenario_outcome_total,
        }
    )

    optim_scenario_outcome = pd.concat(
        {
            "Base": optim_scenario_base_contrib,
            "Marketing": optim_scenario_outcome_total - optim_scenario_base_contrib,
            "Total": optim_scenario_outcome_total,
        }
    )

    outcome_comparison = compare_base_vs_new(
        base_scenario_outcome.rename("Base Scenario"),
        optim_scenario_outcome.rename("Optimal Scenario"),
        pct_scale,
    )
    outcome_comparison = outcome_comparison.unstack(level=0)

    ### Overall comparison

    # Total spend (Budget)
    base_spend = np.sum(base_scenario.values)  # Base Scenario - Total Spend
    optim_spend = np.sum(optimal_scenario.values)  # Optimal Scenario - Total Spend

    # Objective value
    base_obj_val = base_scenario_outcome_total[
        obj_list
    ].sum()  # Objective value at base scenario
    optim_obj_val = optim_scenario_outcome_total[
        obj_list
    ].sum()  # Objective value at optimal scenario

    overall_index = ["Total Spend", optim_input["main_input"]["objective_to_max"]]
    overall_base = pd.Series(
        [base_spend, base_obj_val], index=overall_index, name="Base Scenario"
    )
    overall_optim = pd.Series(
        [optim_spend, optim_obj_val], index=overall_index, name="Optimal Scenario"
    )
    overall_comparison = compare_base_vs_new(overall_base, overall_optim, pct_scale)

    output = {
        "convergence": convergence,
        "overall": overall_comparison,
        "outcome": outcome_comparison,
        "spend": spend_comparison,
        "spend_by_period": spend_by_period,
        "optimal_spend_plan": optimal_spend_plan,
    }
    return output


# %% Save optimization output

number_formats = {
    "dollar_acc": '_-[$$-409]* #,##0_ ;_-[$$-409]* -#,##0 ;_-[$$-409]* "-"_ ;_-@_ ',
    "dollar_B": '$ #,##0,,, "B"',
    "dollar_M": '$ #,##0,, "M"',
    "dollar_K": '$ #,##0, "K"',
    "number": "#,##0",
    "number_K": '#,##0, "K"',
    "number_M": '#,##0,, "M"',
    "number_percent": "0.0%",
}


def write_output_to_excel(output, output_dir, output_file, objective_to_max, n_periods):
    """
    Write optimization output to excel

    Parameters
    ----------
    output : dict
        Dictionary containing all the outputs in `pandas.DataFrame` format.

    output_dir : str
        Output directory in string format.

    output_file : str
        Excel filename to save the optimization output.

    objective_to_max : str
        Objective to maximize; user input in main module.

    n_periods : int
        Number of periods in optimization.
    """
    if output_file is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = objective_to_max + "_maximization_results_" + timestamp + ".xlsx"
    with pd.ExcelWriter(
        os.path.join(output_dir, output_file), engine="xlsxwriter"
    ) as writer:
        wb = writer.book
        fmt_dollar_accounting = wb.add_format(
            {"num_format": number_formats["dollar_acc"]}
        )
        fmt_number = wb.add_format({"num_format": number_formats["number"]})
        fmt_percent = wb.add_format({"num_format": number_formats["number_percent"]})

        # Overall Table
        curr_sheetname = "Overall Summary"
        output["overall"].to_excel(writer, sheet_name=curr_sheetname)
        ws1 = writer.sheets[curr_sheetname]
        ws1.set_column("A:A", 15)  # Index
        ws1.set_column("B:D", 16, fmt_number)  # Base, Optimal, Actual Change
        ws1.set_column("E:E", 10, fmt_percent)  # % Change

        # Outcome Table
        curr_sheetname = "Outcome by Segment"
        output["outcome"].to_excel(writer, sheet_name=curr_sheetname)
        ws2 = writer.sheets[curr_sheetname]
        ws2.set_column("A:A", 15)  # Outcome
        ws2.set_column("B:B", 10)  # Segment
        ws2.set_column("C:E", 16, fmt_number)  # Base Scenario - Base, Marketing, Total
        ws2.set_column(
            "F:H", 16, fmt_number
        )  # Optimal Scenario - Base, Marketing, Total
        ws2.set_column("I:K", 16, fmt_number)  # Actual Change - Base, Marketing, Total
        ws2.set_column("L:N", 10, fmt_percent)  # % Change - Base, Marketing, Total
        ws2.set_zoom(90)

        # Spend Table
        curr_sheetname = "Spend Details"
        output["spend"].to_excel(writer, sheet_name=curr_sheetname, index=False)
        ws3 = writer.sheets[curr_sheetname]
        ws3.set_column("A:A", 25)  # Spend Variable Name
        ws3.set_column("B:B", 25)  # Variable Category
        ws3.set_column("C:C", 65)  # Variable Description
        ws3.set_column(
            "D:F", 16, fmt_dollar_accounting
        )  # Spend Values - Base, Optimal, $ Change
        ws3.set_column("G:G", 10, fmt_percent)  # % Changes
        ws3.freeze_panes(1, 3)
        ws3.set_zoom(90)

        # Spend by Period - long format
        curr_sheetname = "Spend by Period"
        output["spend_by_period"].to_excel(
            writer, sheet_name=curr_sheetname, index=False
        )
        ws4 = writer.sheets[curr_sheetname]
        ws4.set_column("A:A", 25)  # Spend Variable Name
        ws4.set_column("B:B", 25)  # Variable Category
        ws4.set_column("C:C", 65)  # Variable Description
        ws4.set_column("D:D", 12)  # Time Period
        ws4.set_column(
            "E:I", 16, fmt_dollar_accounting
        )  # Spend Values - LB, UB, Base, Optimal, $ Change
        ws4.set_column("J:J", 10, fmt_percent)  # % Changes
        ws4.freeze_panes(1, 4)
        ws4.set_zoom(90)

        curr_sheetname = "Optimal Spend Plan"
        output["optimal_spend_plan"].to_excel(
            writer, sheet_name=curr_sheetname, index=False
        )
        ws5 = writer.sheets[curr_sheetname]
        ws5.set_column("A:A", 25)  # Spend Variable Name
        ws5.set_column("B:B", 65)  # Variable Description
        ws5.set_column(
            "C:F", 16, fmt_dollar_accounting
        )  # Spend Values - LB, UB, Base, Optimal, $ Change)
        ws5.freeze_panes(1, 2)
        ws5.set_zoom(90)

    # writer.save()
    # writer.close()


# %%
