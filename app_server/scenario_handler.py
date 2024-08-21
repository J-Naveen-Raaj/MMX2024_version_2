"""
This module is for handling scenario planning
"""

import calendar as cal
import json
import re
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
from flask_login import current_user
from pandas.tseries.frequencies import to_offset
from pandas.tseries.offsets import DateOffset

from app_server.common_utils_dao import UtilsDAO
from app_server.common_utils_handler import UtilsHandler
from app_server.custom_logger import get_logger
from app_server.database_handler import DatabaseHandler
from app_server.MMOptim.config import WHATIF_YEAR
from app_server.MMOptim.constants import MONTHS
from app_server.optimization_dao import OptimizationDAO
from app_server.scenario_dao import ScenarioDAO
from app_server.session_handler import SessionHandler
from app_server.spendchange_handler import SpendChangeHandler
from app_server.what_if_planner_handler import what_if_planner

logger = get_logger(__name__)


class ScenarioHandler(object):
    def __init__(self):
        self.db_conn = DatabaseHandler().get_database_conn()
        self.optimization_dao = OptimizationDAO(self.db_conn)
        self.conn_without_factory = (
            DatabaseHandler().get_database_conn_without_factory()
        )
        self.scenario_dao = ScenarioDAO(self.db_conn)
        self.common_utils_dao = UtilsDAO(self.db_conn)

    def fetch_user_scenario(self, user_id):
        """
        Method to fetch the list of scenarios of a user
        :param user_id:
        :return: scenario_list = [{},{}]
        """
        try:
            scenario_list = self.scenario_dao.get_user_scenarios(user_id)
            convergence_list = self.scenario_dao.get_convergence_scenarios()
            scenario_names_to_remove = {item['name'] for item in convergence_list}
            scenario_list = [scenario for scenario in scenario_list if scenario['scenario_name'] not in scenario_names_to_remove]
            return scenario_list
        except Exception as e:
            logger.exception("Exception in method fetch_user_scenario %s", str(e))

    def fetch_scenario_list_from_outcome(self):
        """
        Method to fetch scenario list from scenario_outcome table
        :return:scenario_list = [{},{}]
        """
        try:
            scenario_list = self.scenario_dao.get_scenarios_from_outcome()
            convergence_list = self.scenario_dao.get_convergence_scenarios()
            scenario_names_to_remove = {item['name'] for item in convergence_list}
            scenario_list = [scenario for scenario in scenario_list if scenario['scenario_name'] not in scenario_names_to_remove]
            return scenario_list
        except Exception as e:
            logger.exception("Exception in method fetch_user_scenario %s", str(e))

    def fetch_data_for_scenario(
        self, scenario_id=None, scenario_name=None, period_type="quarterly"
    ):
        """
        Method to fetch the spend scenario details from database for any particular scenario
        :param scenario_id:
        :param period_type:
        :return: spend scenario_details = [{}, {}, {}]
        """
        try:
            if scenario_id:
                scenario_details = self.scenario_dao.get_data_for_scenario_id(
                    scenario_id, period_type
                )
            elif scenario_name:
                scenario_details = self.scenario_dao.get_data_for_scenario_name(
                    scenario_name, period_type
                )
            else:
                raise Exception("Invalid arguments")
            return scenario_details
        except Exception as e:
            logger.exception("Exception in method fetch_data_for_scenario %s", str(e))

    def getPeriodType(self, period_name):
        """
        Method to get the period type
        :param period_name:
        :return period_type
        """
        # Define a mapping of period names to their respective types
        period_mapping = {
            "monthly": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "quarterly": ["Q1", "Q2", "Q3", "Q4"],
            "halfyearly": ["H1", "H2"],
            "yearly": ["Year"],
            "weekly": [],  # Weekly periods are handled separately
        }
        
        # Check the period name in the dictionary
        for period_type, periods in period_mapping.items():
            if period_name in periods:
                return period_type

        # Handle weekly periods separately since they start with "W_"
        if period_name.startswith("W_"):
            return "weekly"

        # Return None or raise an exception if the period_name is invalid (optional)
        return None


    def get_initial_user_scenario(self, user_id, scenario_name=None, period_type=None):
        """
        Method to fetch the initial scenario and user details
        :param user_id:
        :return:
        """

        try:
            scenario_details_dict = {}
            period_map = {
                "qtrly": "quarterly",
                "halfyearly": "halfyearly",
                "yearly": "yearly",
                "monthly": "monthly",
                "weekly": "weekly",
            }

            session_obj = SessionHandler()
            scenario_details = session_obj.set_value(
                "spend_scenario_details_updt", None
            )

            if not scenario_details:
                if scenario_name:
                    if period_type:
                        period_type = period_map[period_type]
                        scenario_details = self.fetch_data_for_scenario(
                            scenario_id=scenario_name, period_type=period_type
                        )
                    else:
                        scenario_details = self.fetch_data_for_scenario(
                            scenario_id=scenario_name
                        )
                    session_obj.set_value(
                        "spend_scenario_details_updt",
                        self.scenario_dao.fetch_scenario_data_for_change_by_sid(
                            scenario_name
                        ),
                    )
                else:
                    scenario_list = self.fetch_user_scenario(user_id)
                    for scenario in scenario_list:
                        if scenario["scenario_name"] == "Actuals 2018":
                            break
                    scenario_id = scenario["scenario_id"]
                    scenario_name = scenario["scenario_name"]
                    scenarios = dict(
                        [(x["scenario_id"], x["scenario_name"]) for x in scenario_list]
                    )

                    # scenarios = dict([(scenario_id,scenario_name)])
                    scenario_details_dict.update({"scenario_list": scenarios})
                    if period_type:
                        period_type = period_map[period_type]
                        scenario_details = self.fetch_data_for_scenario(
                            scenario_id=scenario_id, period_type=period_type
                        )
                    else:
                        scenario_details = self.fetch_data_for_scenario(
                            scenario_id=scenario_id
                        )
                    session_obj.set_value(
                        "spend_scenario_details_updt",
                        self.scenario_dao.fetch_scenario_data_for_change_by_sid(
                            scenario_id
                        ),
                    )
                scenario_details_df = pd.DataFrame.from_records(scenario_details)
                scenario_details_df["spend_value"] = scenario_details_df[
                    "spend_value"
                ].astype(float)
                media_hierarchy = pd.DataFrame.from_records(
                    self.scenario_dao.get_media_touchpoints()
                )
                final = []

                media_mask = media_hierarchy["node_id"] < 4000

                # non_flag_mask=~(media_hierarchy["node_name"].str.contains("_FLAGS_"))
                def get_node_category(row):
                    if pd.notna(row["parent_node_id"]):
                        parent_row = media_hierarchy[
                            media_hierarchy["node_id"] == row["parent_node_id"]
                        ]
                        if not parent_row.empty:
                            return parent_row["node_display_name"].values[0]
                    return None

                # Apply the function to create the new column
                media_hierarchy["node_category"] = media_hierarchy.apply(
                    get_node_category, axis=1
                )
                for i, node in media_hierarchy[media_mask].iterrows():
                    # Display only the touchpoints and their corresponding data
                    if node["node_name"] != None:
                        data = scenario_details_df[
                            scenario_details_df["node_name"].isin(eval(node.leaf_nodes))
                        ]
                        group_data = (
                            data[["period_name", "spend_value"]]
                            .groupby("period_name", as_index=False)
                            .sum()
                        )
                        row_spend = {}
                        row_spend["node_id"] = node["node_id"]
                        row_spend["node_name"] = node["node_name"]
                        row_spend["node_disp_name"] = node["node_display_name"]
                        row_spend["node_parent"] = node["parent_node_id"]
                        row_spend["node_seq"] = node["node_seq"]
                        row_spend["node_data"] = dict(group_data.values.tolist())
                        row_spend["node_category"] = node["node_category"]
                        if len(group_data["spend_value"]) != 0:
                            row_spend["node_data"].update(
                                {"Total": group_data["spend_value"].sum()}
                            )
                        else:
                            row_spend["node_data"].update({"Total": 0})

                        final.append(row_spend)

                    # Fill the summary component so that we can get total spends in a particular scenario
                    if node["node_id"] == 2001:
                        data = scenario_details_df[
                            scenario_details_df["node_name"].isin(eval(node.leaf_nodes))
                        ]
                        data["check"] = data["node_name"].apply(
                            lambda x: 1 if "_FLAGS_" not in x else 0
                        )
                        data = data[data["check"] == 1]
                        group_data = (
                            data[["period_name", "spend_value"]]
                            .groupby("period_name", as_index=False)
                            .sum()
                        )
                        summary = {
                            "curntspend": group_data["spend_value"].sum(),
                            "scnriospend": group_data["spend_value"].sum(),
                            "chnginspend": 0,
                        }

                # Sort the list with name "final" by node_name,
                # so as to get alphabetically ordered touchpoint data
                final = sorted(final, key=lambda x: x["node_disp_name"])
                scenario_details_dict.update(
                    {
                        "spendDetaildata": final,
                        "summary": summary,
                        "scenario_name": scenario_name,
                    }
                )

            else:
                parent_scenario = [
                    s
                    for s in scenario_details
                    if s["node_parent"] == 0
                    and s["node_id"] == 1
                    and s["period_type"] == "yearly"
                ]
                df_scenario_details = pd.DataFrame(scenario_details)
                period_type = period_map[period_type]
                fmt_scenario_details = (
                    df_scenario_details[
                        df_scenario_details["period_type"] == period_type
                    ]
                    .groupby(
                        [
                            "node_disp_name",
                            "node_id",
                            "node_name",
                            "node_parent",
                            "node_ref_name",
                            "node_seq",
                            "period_type",
                        ],
                        as_index=False,
                    )
                    .apply(lambda x: dict(zip(x.period_name, x.spend_value)))
                    .reset_index()
                    .rename(columns={0: "node_data"})
                    .sort_values(by=["node_id"], ascending=True)
                )

                for index, row in fmt_scenario_details.iterrows():
                    node_data = row["node_data"]
                    total = sum(float(val) for val in node_data.values())
                    node_data.update({"Total": total})
                    row["node_data"] = node_data

                fmt_scenario_details = fmt_scenario_details.to_json(orient="records")

                if "Total" in parent_scenario[0].keys():
                    key = "Total"
                else:
                    key = "spend_value"

                summary = {
                    "curntspend": parent_scenario[0]["spend_value"],
                    "scnriospend": parent_scenario[0][key],
                    "chnginspend": 0,
                }
                scenario_list = self.fetch_user_scenario(user_id)
                scenarios = dict(
                    [(x["scenario_id"], x["scenario_name"]) for x in scenario_list]
                )
                scenario_details_dict.update({"scenario_list": scenarios})
                scenario_details_dict.update(
                    {
                        "spendDetaildata": json.loads(fmt_scenario_details),
                        "summary": summary,
                        "scenario_name": scenario_name,
                    }
                )
            scenario_details_dict["spendDetaildata"] = list(
                filter(
                    lambda val: "_FLAGS_" not in val["node_name"],
                    scenario_details_dict["spendDetaildata"],
                )
            )
            scenario_details_dict["spendDetaildata"] = sorted(
                scenario_details_dict["spendDetaildata"],
                key=lambda x: (x["node_category"], -x["node_data"]["Total"]),
            )
            return scenario_details_dict
        except Exception as e:
            print(traceback.format_exc())
            logger.exception("Exception in method get_initial_user_scenario %s", str(e))

    def update_spend_scenario(self, period_type, scenario_id, output):
        # simulated_spend = pd.DataFrame(
        #     self.optimization_dao.get_spend_from_spend_scenario_details(
        #         scenario_id, period_type
        #     )
        # )
        output = output.loc[:, ["month", "spend_value", "node_name"]]
        output = output.rename(columns={"month": "period_name"})
        node_mapping = pd.DataFrame.from_records(
            self.scenario_dao.get_variable_node_mapping()
        )
        node_mapping = node_mapping.loc[:, ["variable_id", "variable_name", "node_id"]]
        simulated_spend = (
            pd.merge(
                node_mapping,
                output,
                left_on=["variable_name"],
                right_on=["node_name"],
                how="inner",
            )
            .drop(columns=["variable_name"])
            .drop_duplicates()
        )
        simulated_spend["period"] = "monthly"
        period_type = "monthly"

        print("simulated_spend before update\n", simulated_spend)
        # simulated_spend["period"] = period_type
        if period_type == "monthly":
            period_col = "X_MONTH"
            simulated_spend[period_col] = (
                simulated_spend["period_name"]
                .replace({month: idx + 1 for idx, month in enumerate(MONTHS)})
                .replace({f"M{idx}": idx for idx in range(1, 13)})
                .replace({f"M_{idx}": idx for idx in range(1, 13)})
                .astype("int32")
            )
        elif period_type == "quarterly":
            period_col = "X_QTR"
            simulated_spend[period_col] = (
                simulated_spend["period_name"]
                .replace({f"Q{idx}": idx for idx in range(1, 5)})
                .astype("int32")
            )
        elif period_type == "weekly":
            period_col = "X_DT"
            week_regex = re.compile(
                "W_(?P<week_num>[0-9]{,2}) (?P<year>[0-9]{4})-(?P<month>[a-zA-Z]*)-(?P<week_end_date>[0-9]{,2})"
            )
            week_period = pd.json_normalize(
                simulated_spend["period_name"].map(
                    lambda val: week_regex.match(val).groupdict()
                )
            )
            base_year = week_period["year"].unique()[0]
            base_year = int(base_year)
            freq = "W-SUN"
            weeks_of_base = pd.DataFrame(
                {
                    "date": pd.date_range(
                        datetime(base_year, 1, 1), datetime(base_year, 12, 31)
                    )
                }
            )
            weeks_of_base["count"] = 1
            weeks_of_base["week_end_date"] = (
                weeks_of_base["date"] - to_offset(freq) + to_offset(freq)
            )
            weeks_of_base["days_count"] = weeks_of_base.groupby(["week_end_date"])[
                "count"
            ].transform(sum)
            weeks_of_base["week_period_repr"] = (
                "W_"
                + weeks_of_base["week_end_date"].dt.isocalendar().week.astype(str)
                + " "
                + weeks_of_base["week_end_date"].dt.strftime("%Y")
                + "-"
                + weeks_of_base["week_end_date"].dt.strftime("%b")
                + "-"
                + weeks_of_base["week_end_date"].dt.day.astype(str)
            )
            simulated_spend_daily = pd.merge(
                simulated_spend,
                weeks_of_base,
                left_on=["period_name"],
                right_on=["week_period_repr"],
                how="outer",
            )
            simulated_spend_daily["spend_value"] = (
                simulated_spend_daily["spend_value"]
                / simulated_spend_daily["days_count"]
            )
            simulated_spend_daily[period_col] = simulated_spend_daily[
                "date"
            ] + DateOffset(years=WHATIF_YEAR - base_year)
            simulated_spend = (
                simulated_spend_daily.groupby(
                    ["node_id", pd.Grouper(key=period_col, freq=freq)]
                )
                .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
                .reset_index()
            )
        elif period_type == "yearly":
            period_col = "X_YEAR"
            simulated_spend[period_col] = WHATIF_YEAR

        calendar = pd.DataFrame(self.scenario_dao.get_calendar())
        calendar = calendar.loc[calendar["YEAR"] == WHATIF_YEAR]
        calendar["Week end Date"] = pd.to_datetime(
            calendar["Week end Date"], format="%d-%m-%Y"
        )
        calendar.rename(
            columns={
                "Week end Date": "date",
                "Week_end_Date": "date",
                "month": "X_MONTH",
                "year": "X_YEAR",
                "quarter": "X_QTR",
                "QUARTER": "X_QTR",
                "MONTH": "X_MONTH",
                "YEAR": "X_YEAR",
            },
            inplace=True,
        )
        cal_week_count = calendar.assign(
            X_DT=calendar["date"],
            week_count=(
                calendar.assign(DT=calendar["date"], X_DT=calendar["date"])
                .groupby(period_col)["DT"]
                .transform("count")
            ),
        )

        simulated_spend = pd.merge(
            simulated_spend, cal_week_count, on=[period_col], how="left"
        )
        simulated_spend["spend_value"] = (
            simulated_spend["spend_value"] / simulated_spend["week_count"]
        )
        simulated_spend["week_period_repr"] = (
            "W_"
            + simulated_spend["date"].dt.isocalendar().week.astype(str)
            + " "
            + simulated_spend["date"].dt.strftime("%Y")
            + "-"
            + simulated_spend["date"].dt.strftime("%b")
            + "-"
            + simulated_spend["date"].dt.day.astype(str)
        )

        yearly_simulated_spend = (
            simulated_spend.assign(
                period_type="yearly",
                period_name="Year",  # simulated_spend["X_YEAR"]
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )
        halfyearly_simulated_spend = (
            simulated_spend.assign(
                period_type="halfyearly",
                period_name="H"
                + ((simulated_spend["date"].dt.month >= 6).astype(int) + 1).astype(str),
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )

        quarterly_simulated_spend = (
            simulated_spend.assign(
                period_type="quarterly",
                period_name="Q" + simulated_spend["X_QTR"].astype(str),
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )
        monthly_simulated_spend = (
            simulated_spend.assign(
                period_type="monthly",
                period_name=simulated_spend["X_MONTH"].map(
                    {idx + 1: mon for idx, mon in enumerate(MONTHS)}
                ),
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )
        weekly_simulated_spend = (
            simulated_spend.assign(
                period_type="weekly", period_name=simulated_spend["week_period_repr"]
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )
        concated = pd.concat(
            [
                yearly_simulated_spend,
                halfyearly_simulated_spend,
                quarterly_simulated_spend,
                monthly_simulated_spend,
                weekly_simulated_spend,
            ],
            ignore_index=True,
        )
        concated["scenario_id"] = scenario_id
        concated["period_name"] = concated["period_name"].astype(str)
        self.scenario_dao.delete_spend_scenario_details(int(scenario_id))
        UtilsHandler().insert_dataframe_to_mssql(concated, "spend_scenario_details")

    def update_spend_scenario_1(self, period_type, scenario_id):
        simulated_spend = pd.DataFrame(
            self.optimization_dao.get_spend_from_spend_scenario_details(
                scenario_id, period_type
            )
        )
        print("simulated_spend before update\n", simulated_spend)
        simulated_spend["period"] = period_type
        if period_type == "monthly":
            period_col = "X_MONTH"
            simulated_spend[period_col] = (
                simulated_spend["period_name"]
                .replace({month: idx + 1 for idx, month in enumerate(MONTHS)})
                .replace({f"M{idx}": idx for idx in range(1, 13)})
                .replace({f"M_{idx}": idx for idx in range(1, 13)})
                .astype("int32")
            )
        elif period_type == "quarterly":
            period_col = "X_QTR"
            simulated_spend[period_col] = (
                simulated_spend["period_name"]
                .replace({f"Q{idx}": idx for idx in range(1, 5)})
                .astype("int32")
            )
        elif period_type == "weekly":
            period_col = "X_DT"
            week_regex = re.compile(
                "W_(?P<week_num>[0-9]{,2}) (?P<year>[0-9]{4})-(?P<month>[a-zA-Z]*)-(?P<week_end_date>[0-9]{,2})"
            )
            week_period = pd.json_normalize(
                simulated_spend["period_name"].map(
                    lambda val: week_regex.match(val).groupdict()
                )
            )
            base_year = week_period["year"].unique()[0]
            base_year = int(base_year)
            freq = "W-SUN"
            weeks_of_base = pd.DataFrame(
                {
                    "date": pd.date_range(
                        datetime(base_year, 1, 1), datetime(base_year, 12, 31)
                    )
                }
            )
            weeks_of_base["count"] = 1
            weeks_of_base["week_end_date"] = (
                weeks_of_base["date"] - to_offset(freq) + to_offset(freq)
            )
            weeks_of_base["days_count"] = weeks_of_base.groupby(["week_end_date"])[
                "count"
            ].transform(sum)
            weeks_of_base["week_period_repr"] = (
                "W_"
                + weeks_of_base["week_end_date"].dt.isocalendar().week.astype(str)
                + " "
                + weeks_of_base["week_end_date"].dt.strftime("%Y")
                + "-"
                + weeks_of_base["week_end_date"].dt.strftime("%b")
                + "-"
                + weeks_of_base["week_end_date"].dt.day.astype(str)
            )
            simulated_spend_daily = pd.merge(
                simulated_spend,
                weeks_of_base,
                left_on=["period_name"],
                right_on=["week_period_repr"],
                how="outer",
            )
            simulated_spend_daily["spend_value"] = (
                simulated_spend_daily["spend_value"]
                / simulated_spend_daily["days_count"]
            )
            simulated_spend_daily[period_col] = simulated_spend_daily[
                "date"
            ] + DateOffset(years=WHATIF_YEAR - base_year)
            simulated_spend = (
                simulated_spend_daily.groupby(
                    ["node_id", pd.Grouper(key=period_col, freq=freq)]
                )
                .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
                .reset_index()
            )
        elif period_type == "yearly":
            period_col = "X_YEAR"
            simulated_spend[period_col] = WHATIF_YEAR

        calendar = pd.DataFrame(self.scenario_dao.get_calendar())
        calendar = calendar.loc[calendar["YEAR"] == WHATIF_YEAR]
        calendar["Week end Date"] = pd.to_datetime(
            calendar["Week end Date"], format="%d-%m-%Y"
        )
        calendar.rename(
            columns={
                "Week end Date": "date",
                "Week_end_Date": "date",
                "month": "X_MONTH",
                "year": "X_YEAR",
                "quarter": "X_QTR",
                "QUARTER": "X_QTR",
                "MONTH": "X_MONTH",
                "YEAR": "X_YEAR",
            },
            inplace=True,
        )
        cal_week_count = calendar.assign(
            X_DT=calendar["date"],
            week_count=(
                calendar.assign(DT=calendar["date"], X_DT=calendar["date"])
                .groupby(period_col)["DT"]
                .transform("count")
            ),
        )

        simulated_spend = pd.merge(
            simulated_spend, cal_week_count, on=[period_col], how="left"
        )
        simulated_spend["spend_value"] = (
            simulated_spend["spend_value"] / simulated_spend["week_count"]
        )
        simulated_spend["week_period_repr"] = (
            "W_"
            + simulated_spend["date"].dt.isocalendar().week.astype(str)
            + " "
            + simulated_spend["date"].dt.strftime("%Y")
            + "-"
            + simulated_spend["date"].dt.strftime("%b")
            + "-"
            + simulated_spend["date"].dt.day.astype(str)
        )

        yearly_simulated_spend = (
            simulated_spend.assign(
                period_type="yearly",
                period_name="Year",  # simulated_spend["X_YEAR"]
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )
        halfyearly_simulated_spend = (
            simulated_spend.assign(
                period_type="halfyearly",
                period_name="H"
                + ((simulated_spend["date"].dt.month >= 6).astype(int) + 1).astype(str),
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )

        quarterly_simulated_spend = (
            simulated_spend.assign(
                period_type="quarterly",
                period_name="Q" + simulated_spend["X_QTR"].astype(str),
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )
        monthly_simulated_spend = (
            simulated_spend.assign(
                period_type="monthly",
                period_name=simulated_spend["X_MONTH"].map(
                    {idx + 1: mon for idx, mon in enumerate(MONTHS)}
                ),
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )
        weekly_simulated_spend = (
            simulated_spend.assign(
                period_type="weekly", period_name=simulated_spend["week_period_repr"]
            )
            .groupby(["node_id", "period_type", "period_name"])
            .agg(spend_value=pd.NamedAgg(column="spend_value", aggfunc=sum))
            .reset_index()
        )
        concated = pd.concat(
            [
                yearly_simulated_spend,
                halfyearly_simulated_spend,
                quarterly_simulated_spend,
                monthly_simulated_spend,
                weekly_simulated_spend,
            ],
            ignore_index=True,
        )
        concated["scenario_id"] = scenario_id
        concated["period_name"] = concated["period_name"].astype(str)
        self.scenario_dao.delete_spend_scenario_details(int(scenario_id))
        UtilsHandler().insert_dataframe_to_mssql(concated, "spend_scenario_details")

    def update_optimization_spend_scenario_data_on_output(
        self, scenarios_tbl_id, output
    ):
        output = output.loc[:, ["quarter", "month", "spend_value", "node_name"]]
        output = output.rename(columns={"spend_value": "spend"})
        # self.optimization_dao.delete_optimization_spend_scenario_data(scenarios_tbl_id)
        node_mapping = pd.DataFrame.from_records(
            self.scenario_dao.get_variable_node_mapping()
        )
        node_mapping = node_mapping.loc[:, ["variable_id", "variable_name"]]
        merged = pd.merge(
            node_mapping,
            output,
            left_on=["variable_name"],
            right_on=["node_name"],
            how="inner",
        )
        merged["scenario_id"] = scenarios_tbl_id
        merged = merged.drop(columns=["variable_name", "node_name"])
        merged = merged.drop_duplicates()
        UtilsHandler().insert_dataframe_to_mssql(
            merged, "optimization_spend_scenario_data"
        )

    def update_optimization_spend_scenario_data(self, scenario_id, scenarios_tbl_id):
        weekly_simulated_spend = pd.DataFrame(
            self.optimization_dao.fetch_spend_from_spend_scenario_details(
                scenario_id, period_type="weekly"
            )
        )
        print("weekly simulated spend sum", weekly_simulated_spend["spend"].sum())
        # Create a new "month" column
        week_regex = re.compile(
            "W_(?P<week_num>[0-9]{,2}) (?P<year>[0-9]{4})-(?P<month>[a-zA-Z]*)-(?P<week_end_date>[0-9]{,2})"
        )
        week_period = pd.json_normalize(
            weekly_simulated_spend["period"].map(
                lambda val: week_regex.match(val).groupdict()
            )
        )
        weekly_simulated_spend["month"] = week_period["month"].map(
            {mon: (idx + 1) for idx, mon in enumerate(MONTHS)}
        )
        monthly_simulated_spend = (
            weekly_simulated_spend.groupby(["month", "variable_id"])
            .agg({"spend": sum})
            .reset_index()
        )
        monthly_simulated_spend["scenario_id"] = scenarios_tbl_id
        monthly_simulated_spend["quarter"] = (
            monthly_simulated_spend["month"] - 1
        ) // 3 + 1
        UtilsHandler().insert_dataframe_to_mssql(
            monthly_simulated_spend, "optimization_spend_scenario_data"
        )

    def save_new_scenario(self, user_id, changed_data):
        """
        Method to add a new scenario to the user profile
        :param user_id:
        :param changed_data:{"Quater-1_marketingctivities_new_1":"1,431,153,581",
        "Quater-1_marketingctivities_new_3":"1,431,153,581", "new_scenario_name":"scenario 1",
        "current_scenario_name":"scenario 1"}
        :return:
        """
        try:
            session_obj = SessionHandler()
            spend_scenario_details = session_obj.get_value(
                "spend_scenario_details_updt"
            )

            if not spend_scenario_details:
                raise Exception("No session data: Invalid Request")
            new_scenario_name = changed_data.pop("scenarioName")
            current_scenario_name = changed_data.pop("current_scenario_name")
            occurence_type = changed_data.pop("period_type")
            period_type_mapping = {
                "qtrly": "quarterly",
            }
            occurence_type = period_type_mapping.get(occurence_type, occurence_type)
            values_as_int = [
                int(value.replace(",", "")) for value in changed_data.values()
            ]
            total_sum = sum(values_as_int)
            year = self.scenario_dao.get_year_name(current_scenario_name)
            get_year = int(year[0]["year"])
            self.scenario_dao.create_new_scenario(
                new_scenario_name, user_id, get_year, occurence_type, total_sum
            )
            scenario_id = (
                pd.DataFrame.from_records(self.common_utils_dao.get_scenario_list())
                .tail(1)["scenario_id"]
                .values[0]
            )
            logger.info("new scenario id " + str(scenario_id))
            transaction = self.db_conn.conn.begin()
            c = 0
            ssd = pd.DataFrame(
                columns=[
                    "node_id",
                    "scenario_id",
                    "period_type",
                    "period_name",
                    "spend_value",
                ]
            )
            for scenario in spend_scenario_details:
                node_id = scenario.get("node_id")
                period_type = scenario.get("period_type")
                period_name = scenario.get("period_name")
                spend_value = float(scenario.get("spend_value"))
                # self.scenario_dao.add_new_scenario_detail(
                #     node_id, scenario_id, period_type, period_name, spend_value
                # )
                l = [node_id, scenario_id, period_type, period_name, spend_value]
                ssd.loc[c] = l
                c = c + 1
            ssd.to_sql(
                con=self.db_conn.conn.engine,
                name="spend_scenario_details",
                if_exists="append",
                index=False,
            )
            transaction.commit()
            # self.db_conn.conn.close()
            simulated_spend = pd.DataFrame.from_records(spend_scenario_details)
            simulated_spend["spend_value"] = simulated_spend["spend_value"].astype(
                float
            )
            simulated_spend = simulated_spend.loc[
                simulated_spend["node_name"].notnull()
            ]
            simulated_spend = simulated_spend[
                ["node_id", "period_type", "period_name", "spend_value", "node_name"]
            ]
            simulated_spend["geo"] = "US"
            simulated_spend = simulated_spend.loc[
                simulated_spend["period_type"] == occurence_type
            ]
            final_output, optimization_scenario_outcome = what_if_planner(
                simulated_spend, occurence_type, year=WHATIF_YEAR
            )
            model = pd.read_sql_query(
                "select id from models where active = 1", self.conn_without_factory
            )

            logger.info("Populating optimization table")
            ### Populate optimization tables
            # 1. scenarios (populate with newly generated ID)
            # transaction = self.db_conn.conn.begin()
            current_user.name = 'User'
            self.optimization_dao.create_new_optimized_scenarios(
                new_scenario_name, current_user.name, "Base"
            )
            scenarios_tbl_id = (
                pd.DataFrame.from_records(self.common_utils_dao.get_scenarios())
                .tail(1)["id"]
                .values[0]
            )
            logger.info("new optimized scenario id %s", str(scenarios_tbl_id))
            # self.db_conn.save_db()
            # transaction.commit()
            # 2. Use id generated above to insert spend into optimization_spend_scenario_data
            # at monthly level with variable id
            self.update_spend_scenario(occurence_type, scenario_id, final_output)
            # self.update_optimization_spend_scenario_data(scenario_id, scenarios_tbl_id)
            self.update_optimization_spend_scenario_data_on_output(
                scenarios_tbl_id, final_output
            )

            # 3. Insert KPI data
            # transaction = self.db_conn.conn.begin()
            optimization_scenario_outcome["ScenarioId"] = scenarios_tbl_id
            optimization_scenario_outcome["model_id"] = model["id"][0]
            UtilsHandler().insert_dataframe_to_mssql(
                optimization_scenario_outcome, "optimization_scenario_outcome"
            )
            # optimization_scenario_outcome.to_sql(name = "optimization_scenario_outcome", con = self.conn_without_factory,if_exists = "append", index = False)
            # transaction.commit()
            # self.db_conn.save_db()
            ### End populate optimization table

            final_output["scenario_id"] = scenario_id
            final_output["model_id"] = model["id"][0]

            UtilsHandler().insert_dataframe_to_mssql(final_output, "scenario_outcome")
            # final_output.to_sql(name='scenario_outcome', con=self.conn_without_factory, if_exists='append',index=False)
            logger.info("Scenario is created and run successfully")
            scenario_list = self.fetch_user_scenario(user_id)
            return scenario_list
        except Exception as e:
            print(traceback.format_exc())
            logger.exception("Exception in method save_new_scenario %s", str(e))

    def compute_delta(self, spend_data):
        """
        Method to compute the delta change proportionally in parent and child
        :param spend_data: {"Quater-1_marketingctivities_new_1":"1,431,153,581", "scenario_name":"scenario 1"}
        :return:
        """
        try:
            scenario_id = spend_data.pop("scenario_name")
            period_name = spend_data.pop("period_name")
            period_type = self.getPeriodType(period_name)
            node_id = spend_data.pop("node_id")
            new_val = spend_data.pop("new_val")
            session_obj = SessionHandler()
            spend_scenario_details = session_obj.get_value(
                "spend_scenario_details_updt"
            )
            d = {
                "Q1": "qtrly",
                "Q2": "qtrly",
                "Q3": "qtrly",
                "Q4": "qtrly",
                "Jan": "monthly",
                "Feb": "monthly",
                "Mar": "monthly",
                "Apr": "monthly",
                "May": "monthly",
                "Jun": "monthy",
                "Jul": "monthly",
                "Aug": "monthly",
                "Sep": "monthly",
                "Nov": "monthly",
                "Oct": "monthly",
                "Dec": "monthly",
                "Year": "yearly",
            }
            a1 = self.get_initial_user_scenario("1", scenario_id, d[period_name])
            media_hierarchy = pd.DataFrame(
                self.common_utils_dao.get_select_touchpoints()
            )
            # # Calendar for date to year - quarter - month mapping
            calendardata = self.scenario_dao.get_calendar()
            calendar = pd.DataFrame.from_records(calendardata)
            calendar.rename(
                columns={
                    "Week_end_Date": "Week end Date",
                    "month": "MONTH",
                    "year": "YEAR",
                    "quarter": "QUARTER",
                },
                inplace=True,
            )
            calendar["MONTH"] = calendar["MONTH"].apply(
                lambda x: cal.month_abbr[x]
            )  # For month number to character

            # Get the week count across each month in the dataframe
            week_ratio_df = (
                calendar.groupby(["YEAR", "QUARTER", "MONTH"])
                .size()
                .reset_index(name="Week_Count")
            )
            # Filter for relevant year
            week_ratio_df = week_ratio_df.loc[
                week_ratio_df["YEAR"] == 2022
            ].reset_index(drop=True)

            # Make a dictionary containing total weeks for each quarter
            quarter_week_sum = (
                week_ratio_df.groupby("QUARTER").agg({"Week_Count": sum}).reset_index()
            )
            quarter_week_dict = dict(
                zip(quarter_week_sum["QUARTER"], quarter_week_sum["Week_Count"])
            )

            # Calculate week ratio for each month
            week_ratio_df["Week_Ratio"] = week_ratio_df.apply(
                lambda row: row["Week_Count"] / quarter_week_dict[row["QUARTER"]],
                axis=1,
            )

            if not spend_scenario_details:
                logger.info("No session data")
                spend_scenario_details = (
                    self.scenario_dao.fetch_scenario_data_for_change_by_sid(scenario_id)
                )
            spend_scenario_details_updt = SpendChangeHandler(
                spend_scenario_details
            ).NC2(
                int(node_id),
                float(new_val),
                period_name,
                week_ratio_df,
                media_hierarchy,
            )
            session_obj.set_value(
                "spend_scenario_details_updt", spend_scenario_details_updt
            )
            data = pd.DataFrame(spend_scenario_details_updt)
            nodes = data["node_id"].unique()
            fmt_data = []
            for node in nodes:
                fdata = data[
                    (data["node_id"] == node) & (data["period_type"] == period_type)
                ]
                row = {}
                row["node_id"] = node
                row["node_name"] = fdata.iloc[0]["node_name"]
                row["node_disp_name"] = fdata.iloc[0]["node_disp_name"]
                row["node_parent"] = fdata.iloc[0]["node_parent"]
                row["node_ref_name"] = fdata.iloc[0]["node_ref_name"]
                row["node_seq"] = fdata.iloc[0]["node_seq"]
                row["scenario_id"] = fdata.iloc[0]["scenario_id"]
                row["node_data"] = (
                    fdata[["period_name", "spend_value"]]
                    .set_index("period_name")
                    .T.to_dict(orient="records")[0]
                )
                row["node_data"]["Total"] = fdata.iloc[0]["Total"]
                fmt_data.append(row)
            return {"fmt_data": fmt_data, "summary": a1["summary"]["curntspend"]}
        except Exception as e:
            logger.exception("Exception in method compute_delta %s", str(e))

    def compute_delta_for_imported_scenario(
        self, imported_data, period_type, scenario_id=1
    ):
        try:
            quarterly_columns = [
                "Variable Name",
                "Variable Description",
                "Q1",
                "Q2",
                "Q3",
                "Q4",
            ]
            half_yearly_columns = ["Variable Name", "Variable Description", "H1", "H2"]
            yearly_columns = ["Variable Name", "Variable Description", "Year"]
            monthly_columns = [
                "Variable Name",
                "Variable Description",
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
            ]
            weekly_columns = [
                "Variable Name",
                "Variable Description",
                "W_1",
                "W_2",
                "W_3",
                "W_4",
                "W_5",
                "W_6",
                "W_7",
                "W_8",
                "W_9",
                "W_10",
                "W_11",
                "W_12",
                "W_13",
                "W_14",
                "W_15",
                "W_16",
                "W_17",
                "W_18",
                "W_19",
                "W_20",
                "W_21",
                "W_22",
                "W_23",
                "W_24",
                "W_25",
                "W_26",
                "W_27",
                "W_28",
                "W_29",
                "W_30",
                "W_31",
                "W_32",
                "W_33",
                "W_34",
                "W_35",
                "W_36",
                "W_37",
                "W_38",
                "W_39",
                "W_40",
                "W_41",
                "W_42",
                "W_43",
                "W_44",
                "W_45",
                "W_46",
                "W_47",
                "W_48",
                "W_49",
                "W_50",
                "W_51",
                "W_52",
                "W_53",
            ]
            get_year = self.scenario_dao.get_sceanarioyear(scenario_id)
            get_year = int(get_year[0]["year"])
            if imported_data:
                # file_contents = imported_data.stream.read().decode("utf-8")
                scenario_data = pd.read_csv(imported_data)
                for column in scenario_data.iloc[:, 2:]:
                    if scenario_data[column].dtypes == "object":
                        temp_data = []
                        temp = scenario_data[column].str.strip()
                        temp.fillna(str(0), inplace=True)
                        for item in temp:
                            value = item.strip()
                            if "$" in item:
                                value = value.replace("$", "")
                            value = value.replace("-", "0")
                            value = value.replace(",", "")
                            temp_data.append(value)
                        temp_data = pd.Series(temp_data)
                        scenario_data[column] = temp_data.astype("float64")

                        # temp_data = scenario_data[column].str.strip()
                        # temp_data = temp_data.str.replace('-', '0')
                        # temp_data = temp_data.str.replace(',', '')
                        # temp_data.fillna(0, inplace=True)
                        # temp_data = temp_data.astype('float64')
                        # scenario_data[column] = temp_data
                if len(scenario_data.columns) > 25:
                    weeks_sp = []
                    weeks_or = []
                    for i in scenario_data.drop(
                        ["Variable Name", "Variable Description"], axis=1
                    ).columns:
                        weeks_sp.append(i.split(" ")[0])
                        weeks_or.append(i)
                    scenario_data[weeks_sp] = scenario_data[weeks_or]
                    scenario_data = scenario_data.drop(weeks_or, axis=1)
                if period_type == "qtrly" and not (
                    sorted(list(scenario_data.columns)) == sorted(quarterly_columns)
                ):
                    return {
                        "error": "Incorrect data uploaded for quarterly spend. Please check and re-upload again."
                    }
                elif period_type == "halfyearly" and not (
                    sorted(list(scenario_data.columns)) == sorted(half_yearly_columns)
                ):
                    return {
                        "error": "Incorrect data uploaded for half yearly spend. Please check and re-upload again."
                    }
                elif period_type == "yearly" and not (
                    sorted(list(scenario_data.columns)) == sorted(yearly_columns)
                ):
                    return {
                        "error": "Incorrect data uploaded for yearly spend. Please check and re-upload again."
                    }
                elif period_type == "monthly" and not (
                    sorted(list(scenario_data.columns)) == sorted(monthly_columns)
                ):
                    return {
                        "error": "Incorrect data uploaded for monthly spend. Please check and re-upload again."
                    }
                elif period_type == "weekly" and not (
                    sorted(list(scenario_data.columns)) == sorted(weekly_columns)
                ):
                    return {
                        "error": "Incorrect data uploaded for weekly spend. Please check and re-upload again."
                    }
                scenario_data.rename(
                    columns={
                        "Variable Name": "node_name",
                        "Variable Description": "touchpoint_name",
                    },
                    inplace=True,
                )
            columns = scenario_data.columns

            if "Unnamed: 0" in columns:
                scenario_data.drop(columns="Unnamed: 0", inplace=True)
                columns = scenario_data.columns
            period_name_dict = {
                55: [
                    "W_1",
                    "W_2",
                    "W_3",
                    "W_4",
                    "W_5",
                    "W_6",
                    "W_7",
                    "W_8",
                    "W_9",
                    "W_10",
                    "W_11",
                    "W_12",
                    "W_13",
                    "W_14",
                    "W_15",
                    "W_16",
                    "W_17",
                    "W_18",
                    "W_19",
                    "W_20",
                    "W_21",
                    "W_22",
                    "W_23",
                    "W_24",
                    "W_25",
                    "W_26",
                    "W_27",
                    "W_28",
                    "W_29",
                    "W_30",
                    "W_31",
                    "W_32",
                    "W_33",
                    "W_34",
                    "W_35",
                    "W_36",
                    "W_37",
                    "W_38",
                    "W_39",
                    "W_40",
                    "W_41",
                    "W_42",
                    "W_43",
                    "W_44",
                    "W_45",
                    "W_46",
                    "W_47",
                    "W_48",
                    "W_49",
                    "W_50",
                    "W_51",
                    "W_52",
                    "W_53",
                ],
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
            period_cols = period_name_dict[len(columns)]
            scenario_data[period_cols] = scenario_data[period_cols].fillna(0)
            media_hierarchy = pd.DataFrame(self.scenario_dao.get_media_touchpoints())
            scenario_df = pd.merge(
                media_hierarchy, scenario_data, on="node_name", how="left"
            )

            scenario_df[period_cols] = scenario_df[period_cols].fillna(0)
            scenario_df = scenario_df[scenario_df["node_id"] > 2000]

            for index, row in scenario_df.iterrows():
                for period in period_name_dict[len(columns)]:
                    if row["node_name"] == "":
                        scenario_df.loc[index, period] = scenario_df[
                            scenario_df["node_name"].isin(eval(row["leaf_nodes"]))
                        ][period].sum()

            output = []
            for i, row in scenario_df.iterrows():
                if row["node_name"]:
                    temp = {}
                    temp["node_data"] = row.filter(items=period_cols).to_dict()
                    temp["node_data"]["Total"] = row.filter(items=period_cols).sum()
                    temp["node_id"] = row["node_id"]
                    temp["node_name"] = row["node_name"]
                    temp["node_disp_name"] = row["node_display_name"]
                    temp["node_parent"] = row["parent_node_id"]
                    temp["node_seq"] = row["node_seq"]
                    output.append(temp)

            scenario_df = scenario_df[["node_id"] + period_cols]
            scenario_df.sort_values(by=["node_id"], axis=0, inplace=True)

            # Calendar for date to year - quarter - month mapping
            calendardata = self.scenario_dao.get_calendar()
            calendar = pd.DataFrame.from_records(calendardata)
            calendar.rename(
                columns={
                    "Week_end_Date": "Week end Date",
                    "month": "MONTH",
                    "year": "YEAR",
                    "quarter": "QUARTER",
                },
                inplace=True,
            )
            calendar["MONTH"] = calendar["MONTH"].apply(
                lambda x: cal.month_abbr[x]
            )  # For month number to character

            # Media Hierarchy for merging scenario data
            media_hierarchy = pd.DataFrame(self.scenario_dao.get_media_touchpoints())

            # Get the week count across each month in the dataframe
            week_ratio_df = (
                calendar.groupby(["YEAR", "QUARTER", "MONTH"])
                .size()
                .reset_index(name="Week_Count")
            )
            # Filter for relevant year
            week_ratio_df = week_ratio_df.loc[
                week_ratio_df["YEAR"] == 2022
            ].reset_index(drop=True)

            # Make a dictionary containing total weeks for each quarter
            quarter_week_sum = (
                week_ratio_df.groupby("QUARTER").agg({"Week_Count": sum}).reset_index()
            )
            quarter_week_dict = dict(
                zip(quarter_week_sum["QUARTER"], quarter_week_sum["Week_Count"])
            )

            # Calculate week ratio for each month
            week_ratio_df["Week_Ratio"] = week_ratio_df.apply(
                lambda row: row["Week_Count"] / quarter_week_dict[row["QUARTER"]],
                axis=1,
            )

            columns = [
                i
                for i in scenario_df.columns
                if i
                not in [
                    "node_id",
                    "level1",
                    "level2",
                    "level3",
                    "level4",
                    "level5",
                    "touchpoint_name",
                ]
            ]
            scenario_df = SpendChangeHandler(scenario_df).HigherLevelAggregation(
                columns, get_year
            )
            columns = [
                i
                for i in scenario_df.columns
                if i
                not in [
                    "node_id",
                    "level1",
                    "level2",
                    "level3",
                    "level4",
                    "level5",
                    "touchpoint_name",
                ]
            ]
            scenario_df = SpendChangeHandler(scenario_df).LowerLevelDestribution(
                columns, week_ratio_df, get_year
            )
            columns = [
                i
                for i in scenario_df.columns
                if i
                not in [
                    "level1",
                    "level2",
                    "level3",
                    "level4",
                    "level5",
                    "touchpoint_name",
                ]
            ]
            scenario_df = pd.melt(
                scenario_df[columns],
                id_vars=["node_id"],
                var_name="period_name",
                value_name="spend_value",
            )
            scenario_df = pd.merge(
                scenario_df, media_hierarchy, on="node_id", how="inner"
            )
            scenario_df["period_type"] = scenario_df["period_name"].apply(
                lambda x: self.getPeriodType(x)
            )
            session_obj = SessionHandler()
            session_obj.set_value(
                "spend_scenario_details_updt", scenario_df.to_dict("records")
            )
            if period_type == "weekly":
                output = list(
                    filter(lambda val: "_FLAGS_" not in val["node_name"], output)
                )
                output = list(filter(lambda val: val["node_name"][0:2] == "M_", output))
                nodes_sum = sum(map(lambda d: d["node_data"]["Total"], output))
                return {"output": output, "sum": nodes_sum}

            return output

        except Exception as e:
            logger.exception("Exception in method compute_delta %s", str(e))

    def download_scenario(self, request):
        period_map = {
            "qtrly": "quarterly",
            "halfyearly": "halfyearly",
            "yearly": "yearly",
            "monthly": "monthly",
        }
        period_type = request.get("period_type") or "monthly"
        session_obj = SessionHandler()
        spend_scenario_details = session_obj.get_value("spend_scenario_details_updt")
        scenario_details = pd.DataFrame(spend_scenario_details)
        media_hierarchy = pd.DataFrame.from_records(
            UtilsHandler().fetch_media_hierarchy_touchpoint()
        )
        period_names = UtilsHandler().getPeriodList(period_map[period_type])
        fmt_df = scenario_details[
            scenario_details["period_type"] == period_map[period_type]
        ].pivot(index="node_id", columns="period_name", values="spend_value")
        result = (
            media_hierarchy[media_hierarchy["node_id"] > 2000]
            .merge(fmt_df, on="node_id", how="left")
            .replace(r"^\s*$", np.nan, regex=True)
        )
        base_columns = [
            "node_id",
            "level1",
            "level2",
            "level3",
            "level4",
            "level5",
            "touchpoint_name",
        ]
        required_columns = base_columns + period_names
        return result[required_columns]

    def downloadScenarioPlanningReport(self, scenario_id, period_type):
        """
        Method to fetch the scenario planning report to be downloaded
        :param scenario_id:
        :param period_type:
        :return: scenario_list
        """
        try:
            scenario_list = pd.DataFrame(
                self.scenario_dao.get_scenario_planning_report(scenario_id, period_type)
            )
            scenario_list = scenario_list.rename(
                columns={
                    "variable_name": "Variable Name",
                    "variable_description": "Variable Description",
                }
            )
            scenario_list = scenario_list.rename(
                columns={
                    "Variable_Name": "Variable Name",
                    "Variable_Description": "Variable Description",
                }
            )
            scenario_pivot = scenario_list.pivot_table(
                index=["Variable Name", "Variable Description"],
                columns="period_name",
                values="spend_value",
            ).reset_index()

            scenario_pivot["variable description"] = scenario_pivot[
                "Variable Description"
            ].str.lower()
            scenario_pivot.sort_values("variable description", inplace=True)
            scenario_pivot.drop("variable description", axis=1, inplace=True)

            if period_type == "weekly":
                w_columns = [
                    col for col in scenario_pivot.columns if col.startswith("W_")
                ]
                date_format = "%Y-%b-%d"
                w_columns.sort(
                    key=lambda x: datetime.strptime(x.split(" ")[1], date_format)
                )
                scenario_pivot = scenario_pivot[
                    ["Variable Name", "Variable Description"] + w_columns
                ]
            elif period_type == "monthly":
                columns_order = [
                    "Variable Name",
                    "Variable Description",
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
                ]
                scenario_pivot = scenario_pivot[columns_order]
            scenario_pivot = scenario_pivot[
                (~scenario_pivot["Variable Name"].str.contains("_FLAGS_"))
                & (scenario_pivot["Variable Name"].str.startswith("M_"))
            ].reset_index(drop=True)
            return scenario_pivot
        except Exception as e:
            logger.exception(
                "Exception in method downloadScenarioPlanningReport %s", str(e)
            )
