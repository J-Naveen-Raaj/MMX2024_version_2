"""
This module is for handling optimization
"""

import calendar as cal
import math
import os
import sys
import traceback

import numpy as np
from flask_login import current_user

from app_server.common_utils_dao import UtilsDAO
from app_server.common_utils_handler import UtilsHandler
from app_server.custom_logger import get_logger
from app_server.database_handler import DatabaseHandler
from app_server.MMOptim.config import WHATIF_YEAR
from app_server.MMOptim.constants import MONTHS
from app_server.MMOptim.optim_run import run_optimization_with_UI
from app_server.optimization_dao import OptimizationDAO
from app_server.scenario_dao import ScenarioDAO
from app_server.what_if_planner_handler import what_if_planner
from config import OP_OUTPUT_FILES_DIR

sys.dont_write_bytecode = True
import pandas as pd

logger = get_logger(__name__)

# Define constants
COLUMN_VARIABLE_NAME = "Variable Name"
COLUMN_VARIABLE_DESCRIPTION = "Variable Description"
LOWER_BOUND = "Lower Bound"
SCENARIO_EXISTS_MESSAGE = "Scenario already exist, Please enter new scenario name"
LOWER_BOUND_CALC = "Lower Bound calc"
UPPER_BOUND_CALC = "Upper Bound calc"
LOWER_BOUND_PERCENT = "Lower Bound %"
UPPER_BOUND_PERCENT = "Upper Bound %"
LOWER_BOUND_EFF = "Lower Bound Eff"
UPPER_BOUND_EFF = "Upper Bound Eff"
LOWER_BOUND_DOLLAR = "Lower Bound $"
UPPER_BOUND_DOLLAR = "Upper Bound $"
SQL_SELECT_VARIABLES = "select variable_id,variable_name from variable_node_mapping "
VARIABLE_CATEGORY = "Variable Category"
BASE_SCENARIO = "Base Scenario"
UPPER_BOUND = "Upper Bound"

class OptimizationHandler(object):
    def __init__(self):
        self.db_conn = DatabaseHandler().get_database_conn()
        self.optimization_dao = OptimizationDAO(self.db_conn)
        self.conn_without_factory = (
            DatabaseHandler().get_database_conn_without_factory()
        )
        self.scenario_dao = ScenarioDAO(self.db_conn)
        self.common_dao = UtilsDAO(self.db_conn)

    def get_all_scenario_list(self):
        scenario_list = self.optimization_dao.fetch_all_scenario_list()
        return scenario_list

    def get_base_scenario_list(self):
        scenario_list = self.optimization_dao.fetch_base_scenario_list()
        return scenario_list
    def fetch_optimization_status(self,request_data):
        id = int(request_data["optimization_scenario_id"])
        status = self.optimization_dao.fetch_optimization_scenario_status(id)
        return status
    def get_base_scenario_total_budget(self, request):
        scenario_id = request["scenario_id"]
        period_type = request.get("period_type", "quarter")
        period_start = request.get("period_start")
        period_end = request.get("period_end")
        total_budget = self.optimization_dao.fetch_base_scenario_total_budget(
            scenario_id, period_type, period_start, period_end
        )

        return total_budget

    def get_optimization_type_list(self):
        optimization_types = self.optimization_dao.fetch_optimization_types()
        return optimization_types

    def get_optimization_scenario_list(self):
        optimization_scenarios = self.optimization_dao.fetch_optimization_scenarios()
        return optimization_scenarios

    def get_granular_level_media_touchpoints_list(self):
        scenario_list = (
            self.optimization_dao.fetch_granular_level_media_touchpoints_list()
        )
        return scenario_list

    def get_touchpoint_groups_list(self):
        scenario_list = self.optimization_dao.fetch_touchpoint_groups_list()
        return scenario_list

    def get_optimization_records(self):
        optimization_records = self.optimization_dao.fetch_optimization_records()
        return optimization_records

    def compute_delta_for_imported_scenario(
        self, scenario_data, scenario_id, year=2018
    ):
        try:
            scenario_data.rename(
                columns={
                    COLUMN_VARIABLE_NAME: "node_name",
                    COLUMN_VARIABLE_DESCRIPTION: "touchpoint_name",
                },
                inplace=True,
            )
            scenario_data = scenario_data.rename(
                columns={f"M{idx+1}": month for idx, month in enumerate(MONTHS)}
            )
            columns = scenario_data.columns
            period_name_dict = {
                14: [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
                6: ["Q1", "Q2", "Q3", "Q4"],
                4: ["H1", "H2"],
                3: ["Year"],
            }
            all_period_cols = [v for val in period_name_dict.values() for v in val]
            period_cols = scenario_data.columns.intersection(all_period_cols).to_list()

            # period_cols = period_name_dict[len(columns)]
            scenario_data[period_cols] = scenario_data[period_cols].fillna(0)
            media_hierarchy = pd.DataFrame(self.optimization_dao.get_media_hierarchy())
            scenario_df = pd.merge(
                media_hierarchy, scenario_data, on="node_name", how="left"
            )

            scenario_df.loc[:, period_cols] = scenario_df.loc[:, period_cols].fillna(0)
            scenario_df = scenario_df.loc[scenario_df["node_id"] > 2000]

            ## Fill parent levels by aggregating leaf nodes
            for index, row in scenario_df.iterrows():
                for period in period_cols:
                    if row["node_name"] == "":
                        scenario_df.loc[index, period] = scenario_df[
                            scenario_df["node_name"].isin(eval(row["leaf_nodes"]))
                        ][period].sum()

            scenario_df = scenario_df[["node_id"] + period_cols]
            scenario_df.sort_values(by=["node_id"], axis=0, inplace=True)

            # Calendar for date to year - quarter - month mapping
            calendar = pd.DataFrame.from_records(self.scenario_dao.get_calendar())
            calendar.rename(columns={"Week_end_Date": "Week end Date"}, inplace=True)
            calendar = calendar[calendar["YEAR"] == year].drop(
                ["Week end Date", "YEAR"], axis=1
            )
            calendar["MONTH"] = calendar["MONTH"].map(
                lambda x: cal.month_abbr[x]
            )  # For month number to character

            calendar = calendar.groupby(["QUARTER", "MONTH"]).agg("count").reset_index()
            qtr_week_count = calendar.groupby("QUARTER").agg("sum")
            calendar["WEEK"] = calendar["WEEK"] / qtr_week_count.loc[
                calendar["QUARTER"], "WEEK"
            ].reset_index(drop=True)
            calendar["QUARTER"] = "Q" + calendar["QUARTER"].astype("str")

            scenario_df = pd.melt(
                scenario_df, id_vars="node_id", var_name="variable", value_name="value"
            )

            right_on = "MONTH"
            if scenario_df["variable"].str.startswith("Q").all():
                right_on = "QUARTER"
            scenario_df = pd.merge(
                scenario_df, calendar, left_on="variable", right_on=right_on
            )

            scenario_df["value"] = scenario_df["value"] * scenario_df["WEEK"]
            scenario_df = scenario_df.drop(
                ["variable", "WEEK", "QUARTER"], axis=1
            ).rename(columns={"MONTH": "period_name"})
            scenario_df["period_type"] = "monthly"

            output = scenario_df.copy()

            period_map = {
                "Jan": "Q1",
                "Feb": "Q1",
                "Mar": "Q1",
                "Apr": "Q2",
                "May": "Q2",
                "Jun": "Q2",
                "Jul": "Q3",
                "Aug": "Q3",
                "Sep": "Q3",
                "Oct": "Q4",
                "Nov": "Q4",
                "Dec": "Q4",
            }
            scenario_df["period_name"] = scenario_df["period_name"].map(period_map)
            scenario_df = (
                scenario_df.groupby(["node_id", "period_name"]).agg("sum").reset_index()
            )
            scenario_df["period_type"] = "quarterly"
            output = pd.concat([output, scenario_df])

            period_map = {"Q1": "H1", "Q2": "H1", "Q3": "H2", "Q4": "H2"}
            scenario_df["period_name"] = scenario_df["period_name"].map(period_map)
            scenario_df = (
                scenario_df.groupby(["node_id", "period_name"]).agg("sum").reset_index()
            )
            scenario_df["period_type"] = "halfyearly"
            output = pd.concat([output, scenario_df])

            period_map = {"H1": "Year", "H2": "Year"}
            scenario_df["period_name"] = scenario_df["period_name"].map(period_map)
            scenario_df = (
                scenario_df.groupby(["node_id", "period_name"]).agg("sum").reset_index()
            )
            scenario_df["period_type"] = "yearly"
            output = pd.concat([output, scenario_df])

            output = output.rename(columns={"value": "spend_value"})
            output["scenario_id"] = scenario_id

            return output

        except Exception as e:
            print(traceback.format_exc())
            logger.exception("Exception in method compute_delta %s", str(e))
    def fetch_optimization_scenario_status(self,id):
        get_status= self.optimization_dao.fetch_optimization_scenario_status(id)
        return get_status

    def run_optimization_new(self, request_data, username):
        try:
            logger.info("In run_optimization_new method")

            optimization_scenario_id = request_data
            self.optimization_dao.update_optimization_scenario_status(
                optimization_scenario_id, "Incomplete"
            )
            optimization_scenario_name = pd.read_sql_query(
                "select name from optimization_scenario where id = "
                + str(optimization_scenario_id),
                self.conn_without_factory,
            )

            base_scenario_outcome = (
                self.optimization_dao.get_optimization_base_spend_outcome(
                    optimization_scenario_id
                )
            )

            arguments = [{"optimization_scenario_id": optimization_scenario_id}]
            result = self.db_conn.processquery(
                "select period_year from optimization_scenario where id = :optimization_scenario_id",
                arguments,
            )
            if len(result) == 0:
                year = 2021
                print("Year none, taking default")
            else:
                year = result[0]["period_year"]

            ## If base_scenario_outcome is not there, run what-if for that spend and get the outcome
            ## **** Added for issue where new base scenario is created but attribution numbers are not available for it
            ## *** 23/12/2019 - Kumar
            run_type = self.db_conn.processquery(
                "select optimization_type_id from optimization_scenario where id = :optimization_scenario_id",
                {"optimization_scenario_id": optimization_scenario_id},
            )[0]["optimization_type_id"]

            if (len(base_scenario_outcome) > 0) and (run_type == 2):
                logger.info("Simulation already available!")
                return "Simulation already available!"

            if len(base_scenario_outcome) == 0:
                spend_plan_id = self.optimization_dao.fetch_spend_plan_id(
                    optimization_scenario_id
                )[0]["base_scenario_id"]
                scenario_name = self.db_conn.processquery(
                    "select name from scenarios where id = :spend_plan_id",
                    {"spend_plan_id": spend_plan_id},
                )[0]["name"]

                transaction = self.db_conn.conn.begin()
                spend_scenario_tbl_id = self.optimization_dao.create_new_spend_scenario(
                    scenario_name, "Custom Scenario"
                )
                # self.db_conn.save_db()
                transaction.commit()
                base_spend_plan = pd.DataFrame(
                    self.optimization_dao.fetch_spend_by_id(spend_plan_id, "quarter")
                )
                base_simulated_spend = base_spend_plan.copy()
                base_simulated_spend["geo"] = "US"
                base_simulated_spend["period_type"] = "quarterly"
                base_simulated_spend.rename(
                    columns={COLUMN_VARIABLE_NAME: "node_name"}, inplace=True
                )
                # TODO - Get year from optimization table

                logger.info("Started to run what if code from optimization")
                final_output, base_scenario_outcome = what_if_planner(
                    base_simulated_spend, "quarterly", year
                )
                logger.info("What if code run completed from optimization")

                base_spend_plan["period_name"] = "Q" + base_spend_plan[
                    "period_name"
                ].astype("str")

                base_spend_plan = pd.pivot_table(
                    base_spend_plan,
                    index=[COLUMN_VARIABLE_NAME, COLUMN_VARIABLE_DESCRIPTION],
                    columns="period_name",
                    values="spend_value",
                ).reset_index()

                # Update tables for current spend
                self.update_tables(
                    final_output=final_output,
                    optimization_scenario_outcome=base_scenario_outcome,
                    optimal_spend_plan=base_spend_plan,
                    spend_scenario_tbl_id=spend_scenario_tbl_id,
                    scenarios_tbl_id=spend_plan_id,
                )

            run_type = self.db_conn.processquery(
                "select optimization_type_id from optimization_scenario where id = :optimization_scenario_id",
                {"optimization_scenario_id": optimization_scenario_id},
            )[0]["optimization_type_id"]

            if run_type == 2:
                print("Simulation !")
                return

            ## *** 23/12/2019 - Kumar
            optim_input = self.get_optim_input(optimization_scenario_id)
            optim_input["var_bounds"][LOWER_BOUND] = optim_input["var_bounds"][
                LOWER_BOUND
            ].map(math.floor)
            print("optimization scenarion id", optimization_scenario_id)
            logger.info("Starting to run optimizer")
            (
                convergence,
                output_file,
                log_file,
                optimal_spend_plan,
                final_output,
                optimization_scenario_outcome,
            ) = run_optimization_with_UI(
                optim_input,
                optimization_scenario_name["name"][0],
                base_outcome_split=base_scenario_outcome,
                year=year,
            )
            scenario_name = optimization_scenario_name["name"][0]
            self.update_tables(
                username,
                optimal_spend_plan,
                final_output,
                optimization_scenario_outcome,
                optimization_scenario_id,
                scenario_name=scenario_name,
                year=year,
                convergence=convergence,
            )
            # Fetch all optimization reocrdsn
            optimization_records = self.optimization_dao.fetch_optimization_records()
            return optimization_records
        except Exception:
            print(traceback.format_exc())

    def get_optimization_group_constraints(self, optim_scenario_id):
        group_constraints = self.optimization_dao.fetch_optimization_group_constraints(
            optim_scenario_id
        )
        return group_constraints


    def create_optimization_scenario(self, request):
        logger.info(
            "creating a new optimization scenario with scenario name %s",
            request["scenario_name"],
        )
        scenario_exist = self.optimization_dao.check_optimization_scenario_exist(
            request["scenario_name"]
        )
        current_user.name = 'User'
        if current_user.name:
            if scenario_exist[0]["no_of_scenario"] == 0:
                # transaction =self.db_conn.conn.begin()
                self.optimization_dao.insert_optimization_scenario(
                    request, current_user.name
                )
                record_id = int(
                    pd.DataFrame.from_records(self.common_dao.get_optimization_scenario())
                    .sort_values(by="id")
                    .tail(1)["id"]
                    .values[0]
                )
                return record_id
            else:
                logger.info(
                    "scenario name %s already existing for the optimization scenario",
                    request["scenario_name"],
                )
                return {
                    "status": 303,
                    "message": SCENARIO_EXISTS_MESSAGE,
                }
        else:
            logger.info(
                "token expired please login again",
            )
            return {
                "status": 401,
                "message": "Token expired! Please login again",
            }

    def get_individual_basespends(self, request, period_type):
        results = self.optimization_dao.fetch_individual_basespends(
            request, period_type
        )
        return results

    def save_individual_spend_bounds(self, imported_data, scenario_id, period_type):
        logger.info("In save_individual_spend_bounds method")
        if imported_data:
            imported_data_df = pd.read_csv(imported_data)
            period_columns = [
                col for col in imported_data_df.columns if "period(" in col
            ]
            imported_data_df = imported_data_df.rename(
                columns={col: "period" for col in period_columns}
            )
        print(imported_data_df.columns)
        optimization_type = self.optimization_dao.get_optimization_type(scenario_id)
        optimization_type_id = optimization_type[0]["optimization_type_id"]

        imported_data_df[LOWER_BOUND_CALC] = np.floor(
            imported_data_df["spend"] * (100 + imported_data_df[LOWER_BOUND_PERCENT]) / 100
        )
        imported_data_df[UPPER_BOUND_CALC] = (
            imported_data_df["spend"] * (100 + imported_data_df[UPPER_BOUND_PERCENT]) / 100
        )

        if optimization_type_id == 4:
            imported_data_df[LOWER_BOUND_EFF] = imported_data_df["spend"]
        else:
            # Initialize effective lower bounds equal to base spends
            imported_data_df[LOWER_BOUND_EFF] = imported_data_df["spend"].astype(
                float
            )

            for i in range(0, len(imported_data_df)):
                lb_calc_null = pd.isna(imported_data_df[LOWER_BOUND_CALC][i])
                lb_dollar_null = pd.isna(imported_data_df[LOWER_BOUND_DOLLAR][i])

                if lb_calc_null and lb_dollar_null:
                    imported_data_df[LOWER_BOUND_EFF][i] = imported_data_df["spend"][
                        i
                    ]
                elif lb_calc_null and not lb_dollar_null:
                    imported_data_df[LOWER_BOUND_EFF][i] = imported_data_df[
                        LOWER_BOUND_DOLLAR
                    ][i]
                elif not lb_calc_null and lb_dollar_null:
                    imported_data_df[LOWER_BOUND_EFF][i] = imported_data_df[
                        LOWER_BOUND_CALC
                    ][i]
                else:
                    # In case both calculated and absolute dollar values
                    # are present, take the maximum
                    imported_data_df[LOWER_BOUND_EFF][i] = imported_data_df[
                        LOWER_BOUND_CALC
                    ][i]

                imported_data_df[LOWER_BOUND_DOLLAR][i] = imported_data_df[
                    LOWER_BOUND_EFF
                ][i]

        # Initialize effective upper bounds equal to base spends
        imported_data_df[UPPER_BOUND_EFF] = imported_data_df["spend"].astype(float)

        for i in range(0, len(imported_data_df)):
            ub_calc_null = pd.isna(imported_data_df[UPPER_BOUND_CALC][i])
            ub_dollar_null = pd.isna(imported_data_df[UPPER_BOUND_DOLLAR][i])

            if ub_calc_null and ub_dollar_null:
                imported_data_df[UPPER_BOUND_EFF][i] = imported_data_df["spend"][i]
            elif ub_calc_null and not ub_dollar_null:
                imported_data_df[UPPER_BOUND_EFF][i] = imported_data_df[
                    UPPER_BOUND_DOLLAR
                ][i]
            elif not ub_calc_null and ub_dollar_null:
                imported_data_df[UPPER_BOUND_EFF][i] = imported_data_df[
                    UPPER_BOUND_CALC
                ][i]
            else:
                # In case both calculated and absolute dollar values
                # are present, take the minimum
                imported_data_df[UPPER_BOUND_EFF][i] = imported_data_df[
                    UPPER_BOUND_CALC
                ][i]
            imported_data_df[UPPER_BOUND_DOLLAR][i] = imported_data_df[UPPER_BOUND_EFF][
                i
            ]

        imported_data_df["optimization_scenario_id"] = int(scenario_id)
        imported_data_df["period_type"] = period_type
        imported_data_df.drop(
            columns=[LOWER_BOUND_CALC, UPPER_BOUND_CALC], inplace=True
        )

        # get variable node mapping

        variable_df = pd.read_sql_query(
            SQL_SELECT_VARIABLES,
            self.conn_without_factory,
        )
        # base spends to be overriden by base scenario when not new allocation
        if optimization_type_id != 3:
            base_spends = (
                pd.DataFrame.from_records(
                    self.optimization_dao.fetch_base_scenario_ossd(
                        scenario_id, period_type
                    )
                )
                .rename(
                    columns={
                        "spend_value": "base_spend",
                        "variable_category": "Variable_Category",
                        "variable_description": "Variable_Description",
                        "variable_name": "Variable_Name",
                        "period": "Period",
                    }
                )
                .drop(columns=["Variable_Category", "Variable_Description"])
            )
            imported_data_df = pd.merge(
                imported_data_df,
                base_spends,
                left_on=["variable_name", "period"],
                right_on=["Variable_Name", "Period"],
                how="left",
            ).drop(columns=["Variable_Name", "Period", "spend"])

        results = pd.merge(imported_data_df, variable_df, on="variable_name")

        results.rename(
            columns={
                "base_spend": "spend",
                # "Lower Bound Eff": "lowerbound",
                # "Upper Bound Eff": "upperbound",
            },
            inplace=True,
        )
        print(results.columns)
        for idx, row in results.iterrows():
            self.optimization_dao.update_individual_spend_bounds(row)

        # # Delete existing spend bounds for current scenario
        # # transaction = self.db_conn.conn.begin()
        # self.optimization_dao.delete_existing_individual_spend_bounds(scenario_id)
        # # self.db_conn.save_db()
        # # transaction.commit()
        # # Insert spend bound for current scenario
        # UtilsHandler().insert_dataframe_to_mssql(
        #     results[
        #         [
        #             "optimization_scenario_id",
        #             "variable_id",
        #             "lock",
        #             "period_type",
        #             "period",
        #             "lowerbound",
        #             "upperbound",
        #             "base_spend",
        #         ]
        #     ],
        #     "individual_spend_bounds",
        # )
        # # results[['optimization_scenario_id', 'variable_id', 'lock', 'period', 'lowerbound', 'upperbound']].to_sql(
        # #    name = 'individual_spend_bounds', con = self.conn_without_factory, if_exists = 'append', index = False)

        logger.info(
            "Individual spend bounds saved for the scenario id %s", str(scenario_id)
        )
        imported_data_df = imported_data_df.rename(columns={"base_spend": "spend"})
        if optimization_type_id != 4:
            lower_sum = round(imported_data_df[LOWER_BOUND_DOLLAR].sum(), 0)
        else:
            lower_sum = round(imported_data_df["spend"].sum(), 0)

        upper_sum = round(imported_data_df[UPPER_BOUND_DOLLAR].sum(), 0)

        if optimization_type_id == 3:
            base_sum = round(imported_data_df["spend"].sum(), 0)
        else:
            base_sum = ""
        return (
            imported_data_df.fillna("").to_dict("records"),
            lower_sum,
            upper_sum,
            base_sum,
        )

    def save_individual_spend_bounds_for_opt_scenario(
        self, optimization_scenario_id, request_data
    ):
        result = pd.DataFrame.from_records(
            self.get_individual_basespends(
                optimization_scenario_id, request_data["period_type"]
            )
        )
        result["lock"] = "Yes"
        result[LOWER_BOUND_PERCENT] = ""
        result[UPPER_BOUND_PERCENT] = ""
        result[LOWER_BOUND_DOLLAR] = np.floor(result["spend"])
        result[UPPER_BOUND_DOLLAR] = result["spend"]
        result[LOWER_BOUND_EFF] = np.floor(result["spend"])
        result[UPPER_BOUND_EFF] = result["spend"]
        result["optimization_scenario_id"] = optimization_scenario_id
        result["period_type"] = request_data["period_type"]

        # get variable node mapping

        variable_df = pd.read_sql_query(
            SQL_SELECT_VARIABLES,
            self.conn_without_factory,
        )

        results = pd.merge(result, variable_df, on="variable_name")

        results.rename(
            columns={LOWER_BOUND_EFF: "lowerbound", UPPER_BOUND_EFF: "upperbound"},
            inplace=True,
        )
        # Delete existing spend bounds for current scenario
        # transaction =self.db_conn.conn.begin()
        self.optimization_dao.delete_existing_individual_spend_bounds(
            int(optimization_scenario_id)
        )
        # transaction.commit()
        # self.db_conn.conn.close()
        # Insert spend bound for current scenario
        results = results.rename(columns={"spend": "base_spend"})
        UtilsHandler().insert_dataframe_to_mssql(
            results[
                [
                    "optimization_scenario_id",
                    "variable_id",
                    "lock",
                    "period",
                    "period_type",
                    "lowerbound",
                    "upperbound",
                    "base_spend",
                ]
            ],
            "individual_spend_bounds",
        )
        results = results.rename(columns={"base_spend": "spend"})
        print(self.optimization_dao.fetch_base_scenario(optimization_scenario_id))
        # results[['optimization_scenario_id', 'variable_id', 'lock', 'period', 'lowerbound', 'upperbound']].to_sql(
        #    name = 'individual_spend_bounds', con = self.conn_without_factory, if_exists = 'append', index = False)
        result["lock"] = 1
        result_filtered = result[
            (~result["variable_name"].str.contains("_FLAGS_"))
            & (result["variable_name"].str.startswith("M_"))
        ].reset_index(drop=True)
        period_start = int(request_data["period_start"])
        period_end = int(request_data["period_end"])
        result_filtered = result_filtered[
            (result_filtered["period"] >= period_start)
            & (result_filtered["period"] <= period_end)
        ]
        result_df = (
            result_filtered.groupby(["variable_name", "variable_description"])
            .agg({"spend": "sum"})
            .reset_index()
        )
        result_df_sorted = result_df.sort_values(by="spend", ascending=False)
        result_df_sorted.rename(columns={"spend": "spend_agg"}, inplace=True)
        merged_df = pd.merge(
            result_filtered,
            result_df_sorted[["variable_name", "variable_description", "spend_agg"]],
            on=["variable_name", "variable_description"],
            how="left",
        )

        result_filtered = merged_df.sort_values(
            by=["variable_category", "spend_agg"], ascending=[True, False]
        ).reset_index(drop=True)
        # response= {}
        lower_bound_sum = round(result_filtered[LOWER_BOUND_DOLLAR].sum(), 0)
        upper_bound_sum = round(result_filtered[UPPER_BOUND_DOLLAR].sum(), 0)
        base_spend_sum = round(result_filtered["spend"].sum(), 0)
        results = result_filtered.fillna("").to_dict("records")
        # response["lower_bound_sum"]=lower_bound_sum
        # response["upper_bound_sum"]=upper_bound_sum
        # response["results"]=results
        return results, upper_bound_sum, lower_bound_sum, base_spend_sum

    def update_individual_spend_bounds(self, request):
        # Get the optimization type
        optimization_type = self.optimization_dao.get_optimization_type(
            request["optimization_scenario_id"]
        )
        optimization_type_id = optimization_type[0]["optimization_type_id"]
        if optimization_type_id == 4:
            request["base_spend"] = int(request["spend"])
            request[LOWER_BOUND_EFF] = request[
                "spend"
            ]  # In case of incremental, effective lower bound will not change
        elif request[LOWER_BOUND_PERCENT] != "" and request[LOWER_BOUND_DOLLAR] != "":
            request[LOWER_BOUND_CALC] = np.floor(
                int(request["spend"]) * (100 + int(request[LOWER_BOUND_PERCENT])) / 100
            )
            request[LOWER_BOUND_EFF] = np.floor(request[LOWER_BOUND_CALC])
        elif request[LOWER_BOUND_PERCENT] == "" and request[LOWER_BOUND_DOLLAR] != "":
            request[LOWER_BOUND_EFF] = int(request[LOWER_BOUND_DOLLAR])
        else:
            request[LOWER_BOUND_EFF] = np.floor(
                int(request["spend"]) * (100 + int(request[LOWER_BOUND_PERCENT])) / 100
            )

        if request[UPPER_BOUND_PERCENT] != "" and request[UPPER_BOUND_DOLLAR] != "":
            request[UPPER_BOUND_CALC] = (
                int(request["spend"]) * (100 + int(request[UPPER_BOUND_PERCENT])) / 100
            )
            request[UPPER_BOUND_EFF] = request[UPPER_BOUND_CALC]
        elif request[UPPER_BOUND_PERCENT] == "" and request[UPPER_BOUND_DOLLAR] != "":
            request[UPPER_BOUND_EFF] = int(request[UPPER_BOUND_DOLLAR])
        else:
            request[UPPER_BOUND_EFF] = (
                request["spend"] * (100 + int(request[UPPER_BOUND_PERCENT])) / 100
            )
        request[UPPER_BOUND_DOLLAR] = request[UPPER_BOUND_EFF]
        request[LOWER_BOUND_DOLLAR] = request[LOWER_BOUND_EFF]
        imported_data_df = pd.DataFrame.from_records([request])

        # get variable node mapping

        variable_df = pd.read_sql_query(
            SQL_SELECT_VARIABLES,
            self.conn_without_factory,
        )
        bounds = []
        results = pd.merge(imported_data_df, variable_df, on="variable_name")
        for index, row in results.iterrows():
            if row["lock"] == 1:
                row[UPPER_BOUND_DOLLAR] = int(request["spend"])
                row[UPPER_BOUND_EFF] = row[UPPER_BOUND_DOLLAR]
                row[LOWER_BOUND_DOLLAR] = int(request["spend"])
                row[LOWER_BOUND_EFF] = row[LOWER_BOUND_DOLLAR]
                request[UPPER_BOUND_DOLLAR] = int(request["spend"])
                request[UPPER_BOUND_EFF] = request[UPPER_BOUND_DOLLAR]
                request[LOWER_BOUND_DOLLAR] = int(request["spend"])
                request[LOWER_BOUND_EFF] = request[LOWER_BOUND_DOLLAR]
                request[UPPER_BOUND_PERCENT] = ""
                request[LOWER_BOUND_PERCENT] = ""
                row["lock"] = "Yes"
            else:
                row["lock"] = "No"
            transaction = self.db_conn.conn.begin()
            res = self.optimization_dao.get_individual_spend_bounds_value(row)
            if (
                optimization_type_id == 3
                and (request[UPPER_BOUND_DOLLAR] == int(round(res[0]["base_spend"], 0)))
                or (request[UPPER_BOUND_DOLLAR] + 1 == int(round(res[0]["base_spend"], 0)))
                or (request[UPPER_BOUND_DOLLAR] - 1 == int(round(res[0]["base_spend"], 0)))
            ):
                request[UPPER_BOUND_DOLLAR] = int(request["spend"])
                request[UPPER_BOUND_EFF] = request[UPPER_BOUND_DOLLAR]
                row[UPPER_BOUND_DOLLAR] = int(request["spend"])
                row[UPPER_BOUND_EFF] = row[UPPER_BOUND_DOLLAR]
            if (
                optimization_type_id == 3
                and (request[LOWER_BOUND_DOLLAR] == int(round(res[0]["base_spend"], 0)))
                or (request[LOWER_BOUND_DOLLAR] + 1 == int(round(res[0]["base_spend"], 0)))
                or (request[LOWER_BOUND_DOLLAR] - 1 == int(round(res[0]["base_spend"], 0)))
            ):
                request[LOWER_BOUND_DOLLAR] = int(request["spend"])
                request[LOWER_BOUND_EFF] = request[LOWER_BOUND_DOLLAR]
                row[LOWER_BOUND_DOLLAR] = int(request["spend"])
                row[LOWER_BOUND_EFF] = row[LOWER_BOUND_DOLLAR]
            if len(res) != 0:
                bounds.append(res[0])
            transaction.commit()
            transaction = self.db_conn.conn.begin()
            self.optimization_dao.update_individual_spend_bounds(row)
            transaction.commit()
        return request, bounds, optimization_type_id

    def update_individual_spend_lock_unlock_all(self, request):
        transaction = self.db_conn.conn.begin()
        self.optimization_dao.update_individual_spend_lock_unlock_all(request)
        # self.db_conn.save_db()
        transaction.commit()
        return request

    def get_touchpoints_for_group(self, group_id):
        all_touchpoints = pd.DataFrame.from_records(
            self.optimization_dao.fetch_granular_level_media_touchpoints_list()
        )
        included_touchpoints = pd.DataFrame.from_records(
            self.optimization_dao.fetch_included_touchpoints(group_id)
        )
        excluded_touchpoints = pd.concat(
            [included_touchpoints, all_touchpoints]
        ).drop_duplicates(keep=False)
        return {
            "included_touchpoints": included_touchpoints.to_dict("records"),
            "excluded_touchpoints": excluded_touchpoints.to_dict("records"),
        }

    def save_group_touchpoint_mapping(self, request):
        logger.info(
            "Creating a new touch point group for the group name %s",
            request["group_name"],
        )

        group_name = request["group_name"]
        touchpoints = pd.DataFrame(request["touchpoints"], columns=["variable_id"])

        # create touchpoint group
        self.optimization_dao.create_group(group_name)
        record_id = (
            pd.DataFrame.from_records(
                self.optimization_dao.fetch_touchpoint_groups_list()
            )
            .sort_values(by="id")
            .tail(1)["id"]
            .values[0]
        )

        # add touchpoints to the created group
        touchpoints["group_id"] = record_id
        UtilsHandler().insert_dataframe_to_mssql(
            touchpoints[["group_id", "variable_id"]],
            "touchpoint_group_variable_mapping",
        )
        """
        touchpoints[['group_id', 'variable_id']].to_sql(name = 'touchpoint_group_variable_mapping',
                                                        con = self.conn_without_factory, if_exists = 'append',
                                                        index = False)
        """
        logger.info(
            "New touch point group is created for the group name %s",
            request["group_name"],
        )

        return {"id": record_id, "name": group_name}

    def add_group_constraint(self, request):
        logger.info("In add_group_constraint method")

        # Add group constraint
        # transaction = self.db_conn.conn.begin()
        result = self.optimization_dao.add_group_constraint(request)
        # self.db_conn.save_db()
        # transaction.commit()
        group_constraints = self.optimization_dao.fetch_optimization_group_constraints(
            request["optimization_scenario_id"]
        )
        for constraint in group_constraints:
            constraint["period_type"] = request.get("period_type")
        logger.info(
            "Added a group constraint for the optimization scenario id %s",
            str(request["optimization_scenario_id"]),
        )
        return group_constraints

    def delete_group_constraint(self, request):
        logger.info("In delete_group_constraint method")

        # remove group constraint
        # transaction = self.db_conn.conn.begin()
        result = self.optimization_dao.remove_group_constraint(request)
        # self.db_conn.save_db()
        # transaction.commit()
        group_constraints = self.optimization_dao.fetch_optimization_group_constraints(
            request["optimization_scenario_id"]
        )
        logger.info(
            "Deleted a group constraint for the optimization scenario id %s",
            str(request["optimization_scenario_id"]),
        )
        return group_constraints

    def import_scenario_spends(self, imported_data):
        if imported_data:
            spend_data = pd.read_csv(imported_data)

        variable_df = pd.read_sql_query(
            "select variable_name,mh.variable_id as node_id,m.node_display_name as node_disp_name,m.parent_node_id as node_parent "
            "from variable_node_mapping mh inner join media_hierarchy m on m.node_id = mh.node_id "
            "inner join models mo on mo.version_id = m.version_id and mo.active = 1 ",
            self.conn_without_factory,
        )
        spend_data["Total"] = (
            spend_data["Q1"] + spend_data["Q2"] + spend_data["Q3"] + spend_data["Q4"]
        )
        final_spend = pd.merge(
            variable_df, spend_data, right_on=COLUMN_VARIABLE_NAME, left_on="variable_name"
        )
        return final_spend.to_dict("records")

    def create_base_scenario(self, request_data):
        try:
            logger.info(
                "Creating a new base scenario with the scenario name %s",
                request_data["scenario_name"],
            )

            # create new base scenario id
            scenario_name = request_data["scenario_name"]
            scenario_exist = self.optimization_dao.check_scenario_exist(scenario_name)

            if scenario_exist[0]["no_of_scenario"] == 0:
                transaction = self.db_conn.conn.begin()
                scenario_id = self.optimization_dao.create_new_base_scenario(
                    scenario_name
                )
                # self.db_conn.save_db()
                # transaction.commit()

                # prepare data from new base scenario
                data = []
                for i in request_data["data"].keys():
                    row = {}
                    row_obj = i.split("_")
                    row["variable_id"] = row_obj[1]
                    row["period"] = row_obj[2].replace("Q", "")
                    row["spend"] = request_data["data"][i]
                    if row_obj[2] != "Total":
                        data.append(row)
                data_df = pd.DataFrame.from_records(data)
                data_df["scenario_id"] = scenario_id
                data["period_type"] = "quarter"

                # insert new base scenario data to scenario spend table
                UtilsHandler().insert_dataframe_to_mssql(
                    data_df, "optimization_spend_scenario_data"
                )

                "------- Start : Running whatif once base scenario is created -------"
                base_spend_plan = pd.DataFrame(
                    self.optimization_dao.fetch_spend_by_id(scenario_id, "quarter")
                )
                base_simulated_spend = base_spend_plan.copy()
                base_simulated_spend["geo"] = "US"
                base_simulated_spend["period_type"] = "quarterly"
                base_simulated_spend.rename(
                    columns={COLUMN_VARIABLE_NAME: "node_name"}, inplace=True
                )

                logger.info("Running whatif")
                final_output, optimization_scenario_outcome = what_if_planner(
                    base_simulated_spend, "quarterly", year=WHATIF_YEAR
                )
                model = pd.read_sql_query(
                    "select id from models where active = 1", self.conn_without_factory
                )

                # 1. Insert into spend_scenarios table
                transaction = self.db_conn.conn.begin()
                scenario_id = int(
                    self.scenario_dao.create_new_scenario(scenario_name, 1)
                )
                # self.db_conn.save_db()
                transaction.commit()
                logger.info("new scenario id " + str(scenario_id))

                # 2. Insert KPI results into optimization_scenario_outcome
                optimization_scenario_outcome["ScenarioId"] = scenario_id
                optimization_scenario_outcome["model_id"] = model["id"][0]
                transaction = self.db_conn.conn.begin()
                UtilsHandler().insert_dataframe_to_mssql(
                    optimization_scenario_outcome, "optimization_scenario_outcome"
                )
                # self.db_conn.save_db()
                transaction.commit()

                # 3. Insert whatif output into scenario_outcome table
                transaction = self.db_conn.conn.begin()
                final_output["scenario_id"] = scenario_id
                final_output["model_id"] = model["id"][0]
                UtilsHandler().insert_dataframe_to_mssql(
                    final_output, "scenario_outcome"
                )
                # self.db_conn.save_db()
                transaction.commit()

                # 4. Insert spends into spend_scenario_details table
                transaction = self.db_conn.conn.begin()
                base_spend_plan["period_name"] = "Q" + base_spend_plan[
                    "period_name"
                ].astype("str")
                base_spend_plan = pd.pivot_table(
                    base_spend_plan,
                    index=[COLUMN_VARIABLE_NAME, COLUMN_VARIABLE_DESCRIPTION],
                    columns="period_name",
                    values="spend_value",
                ).reset_index()
                spend_scenario_details = self.compute_delta_for_imported_scenario(
                    base_spend_plan.copy(), scenario_id, 2024
                )
                spend_scenario_details = spend_scenario_details.drop(
                    columns={"DATE"}, errors="ignore"
                )
                UtilsHandler().insert_dataframe_to_mssql(
                    spend_scenario_details, "spend_scenario_details"
                )
                # self.db_conn.save_db()
                transaction.commit()

                logger.info("Scenario is created and ran successfully")
                " ----- End : Ran whatif and updated all the tables ------- "

                return {"id": scenario_id, "name": scenario_name}
            else:
                logger.info(SCENARIO_EXISTS_MESSAGE)
                return {
                    "status": 303,
                    "message": SCENARIO_EXISTS_MESSAGE,
                }

        except Exception as e:
            logger.exception("Exception in method create_base_scenario %s", str(e))

    def getOptimizationScenarioDetails(self, request):
        results = self.optimization_dao.fetch_optimization_scenario_details(request)
        return results

    def get_optim_input(self, optim_scenario_id):
        print(optim_scenario_id)
        main_input = self.optimization_dao.fetch_main_input(optim_scenario_id)[0]
        # main_input["base_scenario_type"] = "Quarterly"
        main_input = pd.Series(
            data=list(main_input.values()), index=list(main_input.keys())
        )
        base_scenario = pd.DataFrame(
            self.optimization_dao.fetch_base_scenario(
                optim_scenario_id, main_input["period_type"]
            )
        )
        rename_map = {
            "variable_name": COLUMN_VARIABLE_NAME,
            "Variable_Name": COLUMN_VARIABLE_NAME,
            "Variable_Category": VARIABLE_CATEGORY,
            "variable_category": VARIABLE_CATEGORY,
            "Variable_Description": COLUMN_VARIABLE_DESCRIPTION,
            "variable_description": COLUMN_VARIABLE_DESCRIPTION,
            "period": "Period",
        }

        base_scenario = base_scenario.rename(columns=rename_map)

        optimization_type = self.optimization_dao.get_optimization_type(
            optim_scenario_id
        )
        optimization_type_id = optimization_type[0]["optimization_type_id"]
        monthly_base_scenario = None
        if optimization_type_id != 3:
            monthly_base_scenario = pd.DataFrame(
                self.optimization_dao.fetch_base_scenario_ossd(
                    optim_scenario_id, "month"
                )
            )
            monthly_base_scenario = monthly_base_scenario.rename(columns=rename_map)
            monthly_base_scenario = monthly_base_scenario.rename(
                columns={"Period": "MONTH"}
            )

        base_scenario = (
            base_scenario.pivot_table(
                columns="Period",
                values="spend_value",
                index=[COLUMN_VARIABLE_NAME, VARIABLE_CATEGORY, COLUMN_VARIABLE_DESCRIPTION],
            )
            .reset_index()
            .set_index(COLUMN_VARIABLE_NAME)
        )
        print("base scenario\n", base_scenario)
        base_scenario["Total"] = base_scenario.loc[
            :, main_input["period_start"] : main_input["period_end"]
        ].sum(axis=1)
        if main_input["period_type"] == "quarter":
            base_scenario = base_scenario.rename(
                columns={idx: f"Q{idx}" for idx in range(1, 5)}
            )
        elif main_input["period_type"] == "month":
            base_scenario = base_scenario.rename(
                columns={idx + 1: mon for idx, mon in enumerate(MONTHS)}
            )

        var_bounds = pd.DataFrame(
            self.optimization_dao.fetch_spend_bounds(
                optim_scenario_id, main_input["period_type"]
            )
        )
        var_bounds = var_bounds.rename(
            columns={
                "variable_name": COLUMN_VARIABLE_NAME,
                "Variable_Name": COLUMN_VARIABLE_NAME,
                "variable_category": VARIABLE_CATEGORY,
                "Variable_Category": VARIABLE_CATEGORY,
                "variable_description": COLUMN_VARIABLE_DESCRIPTION,
                "Variable_Description": COLUMN_VARIABLE_DESCRIPTION,
                "period": "Period",
                "lock": "Lock",
                "base_scenario": BASE_SCENARIO,
                "Base_Scenario": BASE_SCENARIO,
                "upper_bound": UPPER_BOUND ,
                "Upper_Bound": UPPER_BOUND,
                "lower_bound": LOWER_BOUND,
                "Lower_Bound": LOWER_BOUND,
            }
        )

        mask = (var_bounds["Period"] < main_input["period_start"]) | (
            var_bounds["Period"] > main_input["period_end"]
        )
        var_bounds.loc[mask, BASE_SCENARIO] = 0
        if main_input["period_type"] == "quarter":
            var_bounds["Period"] = "Q" + var_bounds["Period"].astype(str)
        elif main_input["period_type"] == "month":
            var_bounds["Period"] = var_bounds["Period"].map(
                {idx + 1: mon for idx, mon in enumerate(MONTHS)}
            )
        var_bounds = var_bounds.set_index([COLUMN_VARIABLE_NAME, "Period"])
        cond = var_bounds["Lock"] == "Yes"
        if np.any(cond):
            # var_bounds.loc[cond, ['Lower Bound (%)', 'Upper Bound (%)']] = 0
            var_bounds.loc[cond, [LOWER_BOUND, UPPER_BOUND]] = var_bounds.loc[
                cond, BASE_SCENARIO
            ]

        var_desc = pd.DataFrame(
            base_scenario[[VARIABLE_CATEGORY, COLUMN_VARIABLE_DESCRIPTION]]
        )

        var_groups = pd.DataFrame(self.optimization_dao.fetch_var_group())
        var_groups = var_groups.set_index("variable_name")
        var_groups_df = var_desc.copy()

        group_list = var_groups.group_name.unique()

        for group in group_list:
            var_groups_df[group] = np.nan

        for index, row in var_groups.iterrows():
            var_groups_df.loc[index, row["group_name"]] = 1

        var_group_cons = pd.DataFrame(
            columns=["Constraint Type", "Period", "Value", "Variable Group"]
        )
        var_group_data = pd.DataFrame(
            self.optimization_dao.fetch_group_constraints(optim_scenario_id)
        )
        var_group_data = var_group_data.rename(
            columns={
                "variable_group": "Variable Group",
                "period": "Period",
                "constraint_type": "Constraint Type",
                "value": "Value",
            }
        )
        var_group_cons = pd.concat([var_group_cons, var_group_data])

        optim_input = {
            "main_input": main_input,
            "monthly_base_scenario": monthly_base_scenario,
            "base_scenario": base_scenario,
            "var_desc": var_desc,
            "var_bounds": var_bounds,
            "var_group": var_groups_df,
            "var_group_cons": var_group_cons,
        }
        return optim_input

    def get_outcome_maximum_list(self):
        results = self.optimization_dao.fetch_outcome_maximum_list()
        return results

    def getOptimizationScenarioOutcomes(self, request):
        optimization_id = request["optimization_scenario_id"]
        base_spend_query = (
            "select sum(spend) as base_spend from optimization_scenario os "
            "inner join scenarios s on s.id = os.base_scenario_id "
            "inner join optimization_spend_scenario_data d on d.scenario_id = s.id "
            "where os.id = " + optimization_id
        )
        optimized_spend_query = (
            "select sum(spend) as optimized_spend from optimization_scenario os "
            "inner join scenarios s on s.id = os.optimized_scenario_id "
            "inner join optimization_spend_scenario_data d on d.scenario_id = s.id "
            "where os.id = " + optimization_id
        )
        base_spend = pd.read_sql_query(base_spend_query, self.conn_without_factory)
        optimized_spend = pd.read_sql_query(
            optimized_spend_query, self.conn_without_factory
        )
        summary = pd.concat([base_spend, optimized_spend], axis=1)
        summary["summary_name"] = "Total Spend"
        summary["change"] = summary["optimized_spend"] - summary["base_spend"]
        summary["%change"] = summary["change"] / summary["base_spend"] * 100

        outcomes = self.optimization_dao.fetch_optimization_scenario_outcomes(
            optimization_id
        )
        scenario_names = self.optimization_dao.fetch_scenario_names(optimization_id)

        return {
            "summary": summary.fillna("NA").to_dict("records"),
            "outcomes": outcomes,
            "scenarioNames": scenario_names,
        }

    def getKPIOutputComparisonData(self, request):
        scenario_one = int(request["scenario_one"])
        scenario_two = int(request["scenario_two"])
        query_outcome1 = """ select scenario_name from spend_scenario where scenario_id = {scenario_one}""".format(
            scenario_one=scenario_one
        )
        query_outcome2 = """ select scenario_name from spend_scenario where scenario_id = {scenario_two}""".format(
            scenario_two=scenario_two
        )
        outcome1 = pd.read_sql_query(query_outcome1, self.conn_without_factory)
        outcome2 = pd.read_sql_query(query_outcome2, self.conn_without_factory)
        outcome1 = outcome1.iloc[0][0]
        outcome2 = outcome2.iloc[0][0]
        query_scenario1 = (
            """ select id from scenarios where name = '{outcome1}'""".format(
                outcome1=outcome1
            )
        )
        query_scenario2 = (
            """ select id from scenarios where name = '{outcome2}'""".format(
                outcome2=outcome2
            )
        )
        scenario1 = pd.read_sql_query(query_scenario1, self.conn_without_factory)
        scenario2 = pd.read_sql_query(query_scenario2, self.conn_without_factory)
        scenario1 = scenario1.iloc[0][0]
        scenario2 = scenario2.iloc[0][0]
        query = """select sc.id,sc.name,o.outcome,o.segment,o.baseattribution,o.marketingattribution,o.baseattribution + o.marketingattribution + o.externalattribution as Total,o.externalattribution
		from optimization_scenario_outcome o
        inner join scenarios sc on sc.id = o.scenarioId
        where sc.id in ({scenario1},{scenario2}) ORDER BY CASE sc.id
        WHEN {scenario1} THEN 0
        WHEN {scenario2} THEN 1
        END """.format(
            scenario1=scenario1, scenario2=scenario2
        )

        outcomes = pd.read_sql_query(query, self.conn_without_factory)

        """
        changes by: Mayank Prakash on 10/06/2022
        devlog E148: calculating Total Asset in KPI Output Comparison and downloading KPI comparison
        new variable for Total Asset is introduced: O_TOTALASSET_IN
        O_TOTALASSET_IN (attributions) = O_EXASSET_IN (attributions) + O_NTFASSET_IN (attributions)
        """
        _outcome = outcomes
        _outcome = pd.DataFrame(_outcome)
        _outcome.rename(
            columns={
                "segment": "Segment",
                "outcome": "Outcome",
                "baseattribution": "BaseAttribution",
                "total": "Total",
                "marketingattribution": "MarketingAttribution",
                "externalattribution": "ExternalAttribution",
            },
            inplace=True,
        )
        for _name in _outcome["name"].unique():
            for _segment in _outcome["Segment"].unique():
                _id = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome2")
                    & (_outcome["Segment"] == _segment)
                ]["id"].values[0]
                ex_base = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome2")
                    & (_outcome["Segment"] == _segment)
                ]["BaseAttribution"]
                ntf_base = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome1")
                    & (_outcome["Segment"] == _segment)
                ]["BaseAttribution"]
                ex_marketing = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome2")
                    & (_outcome["Segment"] == _segment)
                ]["MarketingAttribution"]
                ntf_marketing = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome1")
                    & (_outcome["Segment"] == _segment)
                ]["MarketingAttribution"]
                ex_control = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome2")
                    & (_outcome["Segment"] == _segment)
                ]["ExternalAttribution"]
                ntf_control = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome1")
                    & (_outcome["Segment"] == _segment)
                ]["ExternalAttribution"]
                total_base = ex_base.values[0] + ntf_base.values[0]
                total_marketing = ex_marketing.values[0] + ntf_marketing.values[0]
                total_control = ex_control.values[0] + ntf_control.values[0]
                total_attr = total_base + total_marketing + total_control
                # _outcome.loc[len(_outcome)] = [_id, _name, 'O_TOTALASSET_IN', _segment, total_base, total_marketing,
                #                                total_attr]

        outcomes = _outcome
        outcomes["id"] = outcomes["name"].apply(
            lambda x: scenario_one if x == outcome1 else scenario_two
        )

        return outcomes.to_dict("records")

    def compare_base_vs_new(self, base, new, pct_scale=1):
        if pct_scale not in [1, 100]:
            raise ValueError(
                "Unknown value for 'pct_scale'. It can take value either 1 or 100."
            )
        comparison_table = pd.concat([base, new], axis=1)
        comparison_table["Change"] = new - base
        comparison_table["Change (%)"] = (new / base - 1) * pct_scale
        return comparison_table

    def download_kpi_output_comparison(self, request):
        scenario_one = int(request["scenario_one"])
        scenario_two = int(request["scenario_two"])
        query_outcome1 = """ select scenario_name from spend_scenario where scenario_id = {scenario_one}""".format(
            scenario_one=scenario_one
        )
        query_outcome2 = """ select scenario_name from spend_scenario where scenario_id = {scenario_two}""".format(
            scenario_two=scenario_two
        )
        outcome1 = pd.read_sql_query(query_outcome1, self.conn_without_factory)
        outcome2 = pd.read_sql_query(query_outcome2, self.conn_without_factory)
        outcome1 = outcome1.iloc[0][0]
        outcome2 = outcome2.iloc[0][0]
        query_scenario1 = (
            """ select id from scenarios where name = '{outcome1}'""".format(
                outcome1=outcome1
            )
        )
        query_scenario2 = (
            """ select id from scenarios where name = '{outcome2}'""".format(
                outcome2=outcome2
            )
        )
        scenario1 = pd.read_sql_query(query_scenario1, self.conn_without_factory)
        scenario2 = pd.read_sql_query(query_scenario2, self.conn_without_factory)
        scenario_one = scenario1.iloc[0][0]
        scenario_two = scenario2.iloc[0][0]
        query = """select sc.id,sc.name,o.outcome,o.segment,o.baseattribution,o.externalattribution,o.marketingattribution,o.baseattribution + o.marketingattribution + o.externalattribution as Total
		from optimization_scenario_outcome o
        inner join scenarios sc on sc.id = o.scenarioId
        where sc.id in ({scenario_one},{scenario_two})""".format(
            scenario_one=scenario_one, scenario_two=scenario_two
        )
        outcomes = pd.read_sql_query(query, self.conn_without_factory)
        _outcome = outcomes
        _outcome = pd.DataFrame(_outcome)
        _outcome.rename(
            columns={
                "segment": "Segment",
                "outcome": "Outcome",
                "baseattribution": "BaseAttribution",
                "total": "Total",
                "marketingattribution": "MarketingAttribution",
                "externalattribution": "ExternalAttribution",
            },
            inplace=True,
        )
        for _name in _outcome["name"].unique():
            for _segment in _outcome["Segment"].unique():
                _id = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome2")
                    & (_outcome["Segment"] == _segment)
                ]["id"].values[0]
                ex_base = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome2")
                    & (_outcome["Segment"] == _segment)
                ]["BaseAttribution"]
                ntf_base = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome1")
                    & (_outcome["Segment"] == _segment)
                ]["BaseAttribution"]
                ex_marketing = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome2")
                    & (_outcome["Segment"] == _segment)
                ]["MarketingAttribution"]
                ntf_marketing = _outcome[
                    (_outcome["name"] == _name)
                    & (_outcome["Outcome"] == "outcome1")
                    & (_outcome["Segment"] == _segment)
                ]["MarketingAttribution"]
                total_base = ex_base.values[0] + ntf_base.values[0]
                total_marketing = ex_marketing.values[0] + ntf_marketing.values[0]
                total_attr = total_base + total_marketing
                # _outcome.loc[len(_outcome)] = [_id, _name, 'O_TOTALASSET_IN', _segment, total_base, total_marketing,
                #                                total_attr]

        outcomes = _outcome
        # Renaming columns
        outcomes.rename(
            columns={"Outcome": "outcome", "Segment": "segment"}, inplace=True
        )

        # Filter for first and second scenario and get their scenario names
        first_scenario = outcomes.loc[outcomes["id"] == int(scenario_one)].reset_index(
            drop=True
        )
        scenario_one_name = outcomes.loc[outcomes["id"] == int(scenario_one)][
            "name"
        ].reset_index(drop=True)[0]
        second_scenario = outcomes.loc[outcomes["id"] == int(scenario_two)].reset_index(
            drop=True
        )
        scenario_two_name = outcomes.loc[outcomes["id"] == int(scenario_two)][
            "name"
        ].reset_index(drop=True)[0]

        # Get total for all segments for each outcome for both the scenarios
        first_total = (
            first_scenario.groupby(["outcome"])[
                [
                    "BaseAttribution",
                    "MarketingAttribution",
                    "ExternalAttribution",
                    "Total",
                ]
            ]
            .sum()
            .reset_index(drop=False)
        )
        first_total["segment"] = "Total"
        first_scenario = pd.concat([first_scenario, first_total])
        second_total = (
            second_scenario.groupby(["outcome"])[
                [
                    "BaseAttribution",
                    "MarketingAttribution",
                    "ExternalAttribution",
                    "Total",
                ]
            ]
            .sum()
            .reset_index(drop=False)
        )
        second_total["segment"] = "Total"
        second_scenario = pd.concat([second_scenario, second_total])

        # Get Base attribution for both the scenario's
        first_scenario_base_contrib = first_scenario.set_index(["outcome", "segment"])[
            "BaseAttribution"
        ]
        second_scenario_base_contrib = second_scenario.set_index(
            ["outcome", "segment"]
        )["BaseAttribution"]

        first_scenario_control_contrib = first_scenario.set_index(
            ["outcome", "segment"]
        )["ExternalAttribution"]
        second_scenario_control_contrib = second_scenario.set_index(
            ["outcome", "segment"]
        )["ExternalAttribution"]

        # Get total attribution for both the scenario's
        first_scenario_total = (
            first_scenario.set_index(["outcome", "segment"])["MarketingAttribution"]
            + first_scenario.set_index(["outcome", "segment"])["BaseAttribution"]
            + first_scenario.set_index(["outcome", "segment"])["ExternalAttribution"]
        )
        second_scenario_total = (
            second_scenario.set_index(["outcome", "segment"])["MarketingAttribution"]
            + second_scenario.set_index(["outcome", "segment"])["BaseAttribution"]
            + second_scenario.set_index(["outcome", "segment"])["ExternalAttribution"]
        )
        # Get base, marketing and total attributions for both the scenario's
        first_scenario_outcome = pd.concat(
            {
                "Base": first_scenario_base_contrib,
                "Marketing": first_scenario_total
                - first_scenario_base_contrib
                - first_scenario_control_contrib,
                "External": first_scenario_control_contrib,
                "Total": first_scenario_total,
            }
        )
        second_scenario_outcome = pd.concat(
            {
                "Base": second_scenario_base_contrib,
                "Marketing": second_scenario_total
                - second_scenario_base_contrib
                - first_scenario_control_contrib,
                "External": second_scenario_control_contrib,
                "Total": second_scenario_total,
            }
        )

        # Compare output for both the scenario's
        scenario_comparison = OptimizationHandler().compare_base_vs_new(
            first_scenario_outcome.rename(scenario_one_name),
            second_scenario_outcome.rename(scenario_two_name),
        )
        scenario_comparison = scenario_comparison.unstack(level=0)

        ## Output format for the excel file

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

        # Output file name
        output_file = (
            "KPI Output"
            + "("
            + scenario_one_name
            + "-"
            + scenario_two_name
            + ")"
            + ".xlsx"
        )

        with pd.ExcelWriter(
            os.path.join(OP_OUTPUT_FILES_DIR, output_file), engine="xlsxwriter"
        ) as writer:
            wb = writer.book
            fmt_number = wb.add_format({"num_format": number_formats["number"]})
            fmt_percent = wb.add_format(
                {"num_format": number_formats["number_percent"]}
            )

            # Outcome Table
            curr_sheetname = "KPI Outcome by Segment"
            scenario_comparison.to_excel(writer, sheet_name=curr_sheetname)
            ws2 = writer.sheets[curr_sheetname]
            ws2.set_column("A:A", 15)  # Outcome
            ws2.set_column("B:B", 10)  # Segment
            ws2.set_column(
                "C:E", 16, fmt_number
            )  # Base Scenario - Base, Marketing, Total
            ws2.set_column(
                "F:H", 16, fmt_number
            )  # Optimal Scenario - Base, Marketing, Total
            ws2.set_column(
                "I:K", 16, fmt_number
            )  # Actual Change - Base, Marketing, Total
            ws2.set_column("L:N", 10, fmt_percent)  # % Change - Base, Marketing, Total
            ws2.set_zoom(90)

            # writer.save()
            # writer.close()
        return output_file

    def update_tables(
        self,
        username,
        optimal_spend_plan=None,
        final_output=None,
        optimization_scenario_outcome=None,
        optimization_scenario_id=None,
        scenario_name=None,
        year=2018,
        convergence=True,
        **kwargs,
    ):
        ## get latest model id
        model = pd.read_sql_query(
            "select id from models where active = 1", self.conn_without_factory
        )
        model_id = model["id"][0]

        ## insert spend plans into DB
        # Step 1. Create new row in scenarios
        # Step 2. Create new row in spend_scenarios
        optimization_scenario_name = pd.read_sql_query(
            "select name,base_scenario_id from optimization_scenario where id = "
            + str(optimization_scenario_id),
            self.conn_without_factory,
        )
        sql_query = "select name from scenarios where id = {}".format(
            optimization_scenario_name["base_scenario_id"][0]
        )
        spend_scenario_name = pd.read_sql_query(
            sql_query,
            self.conn_without_factory,
        )
        optimization_scenario_year = self.scenario_dao.get_year_name(
            spend_scenario_name["name"][0]
        )
        if scenario_name is not None:
            # transaction = self.db_conn.conn.begin()
            self.optimization_dao.create_new_optimized_scenario(scenario_name, username)
            scenarios_tbl_id = (
                pd.DataFrame.from_records(self.common_dao.get_scenarios())
                .tail(1)["id"]
                .values[0]
            )
            # transaction.commit()
            # transaction = self.db_conn.conn.begin()
            self.optimization_dao.create_new_spend_scenario(
                scenario_name, optimization_scenario_year[0]["year"]
            )
            spend_scenario_tbl_id = (
                pd.DataFrame.from_records(self.common_dao.get_scenario_list())
                .tail(1)["scenario_id"]
                .values[0]
            )

            # self.db_conn.save_db()
            # transaction.commit()
        else:
            scenarios_tbl_id = kwargs["scenarios_tbl_id"]
            spend_scenario_tbl_id = kwargs["spend_scenario_tbl_id"]

        # Step 3. Insert spend into spend_scenario_details table
        if optimal_spend_plan is not None:
            spend_scenario_details = self.compute_delta_for_imported_scenario(
                optimal_spend_plan.copy(), spend_scenario_tbl_id, year
            )
            spend_scenario_details = spend_scenario_details.drop(
                columns={"DATE"}, errors="ignore"
            )
            # transaction = self.db_conn.conn.begin()
            print("spend scenario details\n", spend_scenario_details)
            UtilsHandler().insert_dataframe_to_mssql(
                spend_scenario_details, "spend_scenario_details"
            )
            # spend_scenario_details.to_sql(name = "spend_scenario_details", con = self.conn_without_factory, if_exists = "append", index = False)
            # self.db_conn.save_db()
            # transaction.commit()

        optimal_spend = pd.read_sql_query(
            "select * from optimization_spend_scenario_data where scenario_id = %s"
            % (scenarios_tbl_id),
            con=self.conn_without_factory,
        )
        # Step 4. Insert spend into optimization_spend_scenario_data table if there is no data
        if len(optimal_spend) == 0:
            optimal_spend = pd.melt(
                optimal_spend_plan,
                id_vars=[COLUMN_VARIABLE_NAME, COLUMN_VARIABLE_DESCRIPTION],
                var_name=["period"],
                value_name="spend",
            )

            variable_df = pd.read_sql_query(
                SQL_SELECT_VARIABLES,
                self.conn_without_factory,
            )

            optimal_spend = pd.merge(
                optimal_spend,
                variable_df,
                left_on=COLUMN_VARIABLE_NAME,
                right_on="variable_name",
            )
            optimal_spend["quarter"] = (
                optimal_spend["period"]
                .replace({month: f"{idx}" for idx, month in enumerate(MONTHS)})
                .str.replace("Q", "")
                .str.replace("M", "")
                .astype(int)
            )

            optimal_spend = pd.concat(
                [
                    optimal_spend.assign(month=(optimal_spend["quarter"] - 1) * 3 + 1),
                    optimal_spend.assign(month=(optimal_spend["quarter"] - 1) * 3 + 2),
                    optimal_spend.assign(month=(optimal_spend["quarter"] - 1) * 3 + 3),
                ]
            )
            # optimal_spend["period_type"] = "quarter"
            optimal_spend["spend"] = optimal_spend["spend"] / 3

            optimal_spend["scenario_id"] = scenarios_tbl_id

            # transaction = self.db_conn.conn.begin()
            UtilsHandler().insert_dataframe_to_mssql(
                optimal_spend[
                    ["scenario_id", "variable_id", "quarter", "month", "spend"]
                ],
                "optimization_spend_scenario_data",
            )

            # optimal_spend[["scenario_id", "variable_id", "period", "spend"]].to_sql(
            #     name="optimization_spend_scenario_data",
            #     con=self.conn_without_factory,
            #     if_exists="append",
            #     index=False,
            # )

            # self.db_conn.save_db()
            # transaction.commit()

        # Step 5. Update optimization scenario with scenario id and filename
        if scenario_name is not None:
            # transaction = self.db_conn.conn.begin()
            self.optimization_dao.update_optimization_scenario_with_optimized_scenario_id(
                scenarios_tbl_id, optimization_scenario_id, scenario_name + ".xlsx"
            )
            # self.db_conn.save_db()
            # transaction.commit()

        # Step 6. Update optimization_scenario_outcome_table
        if optimization_scenario_outcome is not None:
            optimization_scenario_outcome["ScenarioId"] = scenarios_tbl_id
            optimization_scenario_outcome["model_id"] = model_id
            # transaction = self.db_conn.conn.begin()
            UtilsHandler().insert_dataframe_to_mssql(
                optimization_scenario_outcome, "optimization_scenario_outcome"
            )
            # optimization_scenario_outcome.to_sql(name = "optimization_scenario_outcome", con = self.conn_without_factory,if_exists = "append", index = False)
            # self.db_conn.save_db()
            # transaction.commit()

        # Step 7. Update scenario_outcome_table
        if final_output is not None:
            final_output["scenario_id"] = spend_scenario_tbl_id
            final_output["model_id"] = model_id
            # transaction = self.db_conn.conn.begin()
            UtilsHandler().insert_dataframe_to_mssql(final_output, "scenario_outcome")
            # final_output.to_sql(name = 'scenario_outcome', con = self.conn_without_factory, if_exists = 'append',index = False)
            # self.db_conn.save_db()
            # transaction.commit()
            self.optimization_dao.update_optimization_scenario_status(
                optimization_scenario_id, "Completed"
            )
        # Step 8. Update scenario status if not converged
        print("convergence", convergence)
        if not convergence:
            self.optimization_dao.update_optimization_scenario_status(
                optimization_scenario_id, "No solution found"
            )

    def get_base_spend_value_for_group_constraints(self, request_data):
        try:
            # get the variable list for selected group constraint
            variable_id_data_frame = pd.DataFrame.from_records(
                self.optimization_dao.get_variable_id(
                    request_data["touchpoint_groups_id"]
                )
            )
            if len(variable_id_data_frame) == 0:
                return {
                    "status": 200,
                    "message": "No variable node mapping found for the given touch point group",
                }
            variable_id_list = variable_id_data_frame["variable_id"].to_list()
            # get the base spend for the group constraint for the selected base scenario
            base_spend_for_group_constraint = (
                self.optimization_dao.get_base_spend_for_group_constraint(
                    variable_id_list,
                    request_data["base_scenario_id"],
                    request_data["grp_period"],
                    request_data["period_type"],
                    request_data["period_start"],
                    request_data["period_end"],
                )
            )
            return base_spend_for_group_constraint

        except Exception as e:
            logger.exception(
                "Exception in method get_base_spend_value_for_group_constraints %s",
                str(e),
            )
