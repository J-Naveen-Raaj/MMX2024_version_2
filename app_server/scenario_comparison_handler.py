"""
This module is for handling scenario comparison
"""

import time

import numpy as np
import pandas as pd

from app_server.custom_logger import get_logger
from app_server.database_handler import DatabaseHandler
from app_server.scenario_comparison_dao import ScenarioComparisonDAO
from app_server.WaterfallChart import getWaterfallChartData

logger = get_logger(__name__)

EXTERNAL_FACTORS_MARKETING_BASE = 'External Factors/Marketing/Base'
SPEND_EFFECT = "Spend Effect"
EFFICIENCY_EFFECT = "Efficiency Effect"

class ScenarioComparisonHandler(object):
    def __init__(self):
        self.db_conn = DatabaseHandler().get_database_conn()
        self.scenario_comparison_dao = ScenarioComparisonDAO(self.db_conn)
        self.df = pd.DataFrame()

    def ParentNodeAggegation(self, node, d, col):
        if self.df[(self.df["node_id"] == node)][col].isna().sum() > 0:
            self.df.loc[(self.df["node_id"] == node), col] = 0

        self.df.loc[(self.df["node_id"] == node), col] = (
            self.df.loc[(self.df["node_id"] == node), col] + d
        )

        if len(self.df[(self.df["node_id"] == node)]["parent_node_id"]) > 0:
            if (
                self.df[(self.df["node_id"] == node)]["parent_node_id"].iloc[0] == 0
            ):  # change to null or nan
                return self.df
            else:
                return self.ParentNodeAggegation(
                    self.df[(self.df["node_id"] == node)]["parent_node_id"].iloc[0],
                    d,
                    col,
                )
        else:
            return self.df

    def Parentnodechange(self, node, col):
        """
        For a given node & period_name changes Parent node value
        :param node:
        :param col:
        :return:
        """
        if (len(self.df[self.df["parent_node_id"] == node]) > 0) & (
            self.df[self.df["parent_node_id"] == node][col].isna().sum() == 0
        ):
            total = self.df[(self.df["parent_node_id"] == node)][col].sum()
            self.df.loc[self.df["node_id"] == node, col] = total
            if node != 0:
                parent_node = self.df[self.df["node_id"] == node][
                    "parent_node_id"
                ].iloc[0]
                self.ParentNodeAggegation(parent_node, total, col)
            return self.df

        else:
            nodes = self.df[
                (self.df["parent_node_id"] == node) & (self.df["node_name"].isna())
            ]["node_id"].unique()
            for node in nodes:
                self.Parentnodechange(node, col)
            return self.df

    def fetch_spend_comparison_data(self, request_data):
        starttime = time.time()
        logger.info("Scenario Comparison: data preparation for comparison is started")
        scenario_1 = int(request_data["scenario_1"]) or 1
        scenario_2 = int(request_data["scenario_2"]) or 2
        period_type = request_data["period_type"] or "year"
        outcome = request_data["outcome"] or "outcome2"
        if period_type == "quarter":
            quarter = request_data["quarter"]
        elif period_type == "month":
            quarter = request_data["month"]
        is_required_control = request_data["required_control"]
        if outcome == "outcome2":
            outcome = "outcome2"
        elif outcome == "outcome1":
            outcome = "outcome1"

        # if is_required_control:
        #     node_id = 2000
        else:
            node_id = 2000

        s1_results = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations(
                scenario_1, outcome, period_type
            )
        )
        s2_results = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations(
                scenario_2, outcome, period_type
            )
        )

        s1_spends = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_details(
                scenario_1, period_type
            )
        )
        s2_spends = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_details(
                scenario_2, period_type
            )
        )

        media_hierarchy = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_media_hierarchy()
        ).sort_values(by=["node_seq", "node_id"])

        def lnc(x):
            if x[0] == 2001:
                s = "["
                a = eval(x[1])
                for i in a:
                    if "_FLAGS_" in i:
                        continue
                    else:
                        s = s + "'" + i + "', "
                s = s + "]"
                return s

            return x[1]

        media_hierarchy["leaf_nodes"] = media_hierarchy[
            ["node_id", "leaf_nodes"]
        ].apply(lnc, axis=1)
        media_hierarchy["check"] = media_hierarchy["leaf_nodes"].apply(
            lambda x: 1 if "_FLAGS_" not in str(x) else 0
        )
        media_hierarchy = media_hierarchy[media_hierarchy["check"] == 1]
        media_hierarchy = media_hierarchy.drop("check", axis=1)

        media_hierarchy["leaf_nodes"] = media_hierarchy["leaf_nodes"].map(eval)
        spend_allocation1 = media_hierarchy.merge(
            s1_results, on="node_name", how="left"
        ).replace(r"^\s*$", np.nan, regex=True)
        spend_allocation1 = spend_allocation1.rename(
            index=str,
            columns={
                "node_display_name": "node_disp_name",
                "parent_node_id": "node_parent",
            },
        )
        spend_allocation1 = spend_allocation1.sort_values(
            by=["node_seq", "node_id"], ascending=[True, True]
        )

        spend_allocation2 = media_hierarchy.merge(
            s2_results, on="node_name", how="left"
        ).replace(r"^\s*$", np.nan, regex=True)
        spend_allocation2 = spend_allocation2.rename(
            index=str,
            columns={
                "node_display_name": "node_disp_name",
                "parent_node_id": "node_parent",
            },
        )
        spend_allocation2 = spend_allocation2.sort_values(
            by=["node_seq", "node_id"], ascending=[True, True]
        )

        period_master = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_period_master_data(period_type)
        )

        periods = period_master["period_name"].unique()

        headers = self.get_tree_table_headers([scenario_1, scenario_2], periods)

        final = {"spends": [], "outcomes": [], "headers": headers, "cpa": []}

        for i, node in media_hierarchy[media_hierarchy["node_id"] > node_id].iterrows():
            data1 = spend_allocation1[
                spend_allocation1["node_name"].isin(node.leaf_nodes)
            ]
            data2 = spend_allocation2[
                spend_allocation2["node_name"].isin(node.leaf_nodes)
            ]
            spend1 = s1_spends[s1_spends["node_name"].isin(node.leaf_nodes)]
            spend2 = s2_spends[s2_spends["node_name"].isin(node.leaf_nodes)]

            group_data_s1 = (
                data1[[period_type, "allocation"]]
                .groupby(period_type, as_index=False)[["allocation"]]
                .sum()
                .values.tolist()
            )
            group_data_s2 = (
                data2[[period_type, "allocation"]]
                .groupby(period_type, as_index=False)[["allocation"]]
                .sum()
                .values.tolist()
            )
            group_spend_s1 = (
                spend1[[period_type, "spend_value"]]
                .groupby(period_type, as_index=False)[["spend_value"]]
                .sum()
                .values.tolist()
            )
            group_spend_s2 = (
                spend2[[period_type, "spend_value"]]
                .groupby(period_type, as_index=False)[["spend_value"]]
                .sum()
                .values.tolist()
            )

            row_spend = {}
            row_spend["node_id"] = node["node_id"]
            row_spend["node_name"] = node["node_name"]
            row_spend["node_disp_name"] = node["node_display_name"]
            row_spend["node_parent"] = node["parent_node_id"]
            row_spend["node_seq"] = node["node_seq"]
            row_spend["node_data"] = {}
            node_data_s1 = dict(group_spend_s1)
            node_data_s2 = dict(group_spend_s2)
            node_data_s1.update(node_data_s2)
            row_spend["node_data"] = node_data_s1
            final["spends"].append(row_spend)

            row_outcome = {}
            row_outcome["node_id"] = node["node_id"]
            row_outcome["node_name"] = node["node_name"]
            row_outcome["node_disp_name"] = node["node_display_name"]
            row_outcome["node_parent"] = node["parent_node_id"]
            row_outcome["node_seq"] = node["node_seq"]

            node_data_o1 = dict(group_data_s1)
            node_data_o2 = dict(group_data_s2)
            node_data_o1.update(node_data_o2)
            row_outcome["node_data"] = node_data_o1
            final["outcomes"].append(row_outcome)

            row_outcome1 = {}
            row_outcome1["node_id"] = node["node_id"]
            row_outcome1["node_name"] = node["node_name"]
            row_outcome1["node_disp_name"] = node["node_display_name"]
            row_outcome1["node_parent"] = node["parent_node_id"]
            row_outcome1["node_seq"] = node["node_seq"]
            group_data_outcome11 = group_data_s1.copy()
            if group_data_s1 == [] or group_spend_s1 == []:
                group_data_outcome11 = []
            else:
                for i in range(len(group_spend_s1)):
                    try:
                        if group_data_s1[i][1] == 0:
                            group_data_outcome11[i][1] = 0
                        else:
                            group_data_outcome11[i][1] = group_spend_s1[i][1] / group_data_s1[i][1]
                    # except:
                    #     group_data_outcome11[i][1] = group_data_s1[i][1]
                    except:
                        group_data_outcome11[i][1] = group_data_s1[i][1]
                        raise
            group_data_outcome12 = group_data_s2.copy()
            if group_data_s2 == [] or group_spend_s2 == []:
                group_data_outcome12 = []
            else:
                for i in range(len(group_spend_s2)):
                    try:
                        if group_data_s2[i][1] == 0:
                            group_data_outcome12[i][1] = 0
                        else:
                            group_data_outcome12[i][1] = group_spend_s2[i][1] / group_data_s2[i][1]
                    # except:
                    #     group_data_outcome12[i][1] =  group_data_s2[i][1]
                    except:
                        group_data_outcome12[i][1] =  group_data_s2[i][1]
                        raise
            node_data_o1 = dict(group_data_outcome11)
            node_data_o2 = dict(group_data_outcome12)
            node_data_o1.update(node_data_o2)
            row_outcome1["node_data"] = node_data_o1
            final["cpa"].append(row_outcome1)

        endtime = time.time()
        logger.info(
            "Scenario Comparison: data preparation for comparison is completed in %s",
            (endtime - starttime),
        )
        if period_type != "year":
            d = final
            d1 = dict()
            d1["headers"] = dict()
            d1["headers"]["outcome1"] = []
            d1["headers"]["outcome2"] = []
            for i in d["headers"]["outcome1"]:
                if quarter in i["key"]:
                    d1["headers"]["outcome1"].append(i)
                if i["key"] == "percent":
                    d1["headers"]["outcome1"].append(i)
            for i in d["headers"]["outcome2"]:
                if quarter in i["key"]:
                    d1["headers"]["outcome2"].append(i)
                if i["key"] == "percent":
                    d1["headers"]["outcome2"].append(i)
            d1["spends"] = []
            for i in d["spends"]:
                if len(i["node_data"]) == 0:
                    d1["spends"].append(i)
                else:
                    d2 = dict()
                    d2["node_data"] = dict()
                    for j in i["node_data"].keys():
                        if quarter in j:
                            d2["node_data"][j] = i["node_data"][j]
                    d2["node_disp_name"] = i["node_disp_name"]
                    d2["node_id"] = i["node_id"]
                    d2["node_name"] = i["node_name"]
                    d2["node_parent"] = i["node_parent"]
                    d2["node_seq"] = i["node_seq"]
                    d1["spends"].append(d2)
            d1["outcomes"] = []
            for i in d["outcomes"]:
                if len(i["node_data"]) == 0:
                    d1["outcomes"].append(i)
                else:
                    d2 = dict()
                    d2["node_data"] = dict()
                    for j in i["node_data"].keys():
                        if quarter in j:
                            d2["node_data"][j] = i["node_data"][j]
                    d2["node_disp_name"] = i["node_disp_name"]
                    d2["node_id"] = i["node_id"]
                    d2["node_name"] = i["node_name"]
                    d2["node_parent"] = i["node_parent"]
                    d2["node_seq"] = i["node_seq"]
                    d1["outcomes"].append(d2)
            d1["cpa"] = []
            for i in d["cpa"]:
                if len(i["node_data"]) == 0:
                    d1["cpa"].append(i)
                else:
                    d2 = dict()
                    d2["node_data"] = dict()
                    for j in i["node_data"].keys():
                        if quarter in j:
                            d2["node_data"][j] = i["node_data"][j]
                    d2["node_disp_name"] = i["node_disp_name"]
                    d2["node_id"] = i["node_id"]
                    d2["node_name"] = i["node_name"]
                    d2["node_parent"] = i["node_parent"]
                    d2["node_seq"] = i["node_seq"]
                    d1["cpa"].append(d2)
            final = d1
        spend_percent = []
        for i in final["spends"]:
            if period_type == "year":
                if i["node_data"]["Year_" + str(scenario_1)] == 0:
                    i["node_data"]["percent"] = 0
                else:
                    i["node_data"]["percent"] = round((
                        (
                            i["node_data"]["Year_" + str(scenario_2)]
                            - i["node_data"]["Year_" + str(scenario_1)]
                        )
                        / i["node_data"]["Year_" + str(scenario_1)]
                    ) * 100,2)
                spend_percent.append(i)
            # elif period_type == "quarter":
            #     if i["node_data"][quarter + "_" + str(scenario_1)] == 0:
            #         i["node_data"]["percent"] = 0
            #     else:
            #         i["node_data"]["percent"] = round((
            #             (
            #                 i["node_data"][quarter + "_" + str(scenario_2)]
            #                 - i["node_data"][quarter + "_" + str(scenario_1)]
            #             )
            #             / i["node_data"][quarter + "_" + str(scenario_1)]
            #         ) * 100,2)
            #     spend_percent.append(i)
            # elif period_type == "month":
            #     if i["node_data"][quarter + "_" + str(scenario_1)] == 0:
            #         i["node_data"]["percent"] = 0
            #     else:
            #         i["node_data"]["percent"] = round((
            #             (
            #                 i["node_data"][quarter + "_" + str(scenario_2)]
            #                 - i["node_data"][quarter + "_" + str(scenario_1)]
            #             )
            #             / i["node_data"][quarter + "_" + str(scenario_1)]
            #         ) * 100,2)
            #     spend_percent.append(i)
            elif period_type in ["quarter", "month"]:
                if i["node_data"][quarter + "_" + str(scenario_1)] == 0:
                    i["node_data"]["percent"] = 0
                else:
                    i["node_data"]["percent"] = round((
                        (
                            i["node_data"][quarter + "_" + str(scenario_2)]
                            - i["node_data"][quarter + "_" + str(scenario_1)]
                        )
                        / i["node_data"][quarter + "_" + str(scenario_1)]
                    ) * 100, 2)
                spend_percent.append(i)
        final["spends"] = spend_percent
        outcome_percent = []
        for i in final["outcomes"]:
            if period_type == "year":
                if i["node_data"]["Year_" + str(scenario_1)] == 0:
                    i["node_data"]["percent"] = 0
                else:
                    i["node_data"]["percent"] = round((
                        (
                            i["node_data"]["Year_" + str(scenario_2)]
                            - i["node_data"]["Year_" + str(scenario_1)]
                        )
                        / i["node_data"]["Year_" + str(scenario_1)]
                    ) * 100,2)
                outcome_percent.append(i)
            # elif period_type == "quarter":
            #     if i["node_data"][quarter + "_" + str(scenario_1)] == 0:
            #         i["node_data"]["percent"] = 0
            #     else:
            #         i["node_data"]["percent"] = round((
            #             (
            #                 i["node_data"][quarter + "_" + str(scenario_2)]
            #                 - i["node_data"][quarter + "_" + str(scenario_1)]
            #             )
            #             / i["node_data"][quarter + "_" + str(scenario_1)]
            #         ) * 100,2)
            #     outcome_percent.append(i)
            # elif period_type == "month":
            #     if i["node_data"][quarter + "_" + str(scenario_1)] == 0:
            #         i["node_data"]["percent"] = 0
            #     else:
            #         i["node_data"]["percent"] =round((
            #             (
            #                 i["node_data"][quarter + "_" + str(scenario_2)]
            #                 - i["node_data"][quarter + "_" + str(scenario_1)]
            #             )
            #             / i["node_data"][quarter + "_" + str(scenario_1)]
            #         ) * 100,2)
            #     outcome_percent.append(i)
            elif period_type in ["quarter", "month"]:
                if i["node_data"][quarter + "_" + str(scenario_1)] == 0:
                    i["node_data"]["percent"] = 0
                else:
                    i["node_data"]["percent"] = round((
                        (
                            i["node_data"][quarter + "_" + str(scenario_2)]
                            - i["node_data"][quarter + "_" + str(scenario_1)]
                        )
                        / i["node_data"][quarter + "_" + str(scenario_1)]
                    ) * 100, 2)
                outcome_percent.append(i)
        final["outcomes"] = outcome_percent
        cpa_percent = []
        for i in final["cpa"]:
            if period_type == "year":
                if i["node_data"]["Year_" + str(scenario_1)] == 0:
                    i["node_data"]["percent"] = 0
                else:
                    i["node_data"]["percent"] = round((
                        (
                            i["node_data"]["Year_" + str(scenario_2)]
                            - i["node_data"]["Year_" + str(scenario_1)]
                        )
                        / i["node_data"]["Year_" + str(scenario_1)]
                    ) * 100,2)
                cpa_percent.append(i)
            # elif period_type == "quarter":
            #     if i["node_data"][quarter + "_" + str(scenario_1)] == 0:
            #         i["node_data"]["percent"] = 0
            #     else:
            #         i["node_data"]["percent"] = round((
            #             (
            #                 i["node_data"][quarter + "_" + str(scenario_2)]
            #                 - i["node_data"][quarter + "_" + str(scenario_1)]
            #             )
            #             / i["node_data"][quarter + "_" + str(scenario_1)]
            #         ) * 100,2)
            #     cpa_percent.append(i)
            # elif period_type == "month":
            #     if i["node_data"][quarter + "_" + str(scenario_1)] == 0:
            #         i["node_data"]["percent"] = 0
            #     else:
            #         i["node_data"]["percent"] = round((
            #             (
            #                 i["node_data"][quarter + "_" + str(scenario_2)]
            #                 - i["node_data"][quarter + "_" + str(scenario_1)]
            #             )
            #             / i["node_data"][quarter + "_" + str(scenario_1)]
            #         ) * 100,2)
            #     cpa_percent.append(i)
            elif period_type in ["quarter", "month"]:
                if i["node_data"][quarter + "_" + str(scenario_1)] == 0:
                    i["node_data"]["percent"] = 0
                else:
                    i["node_data"]["percent"] = round((
                        (
                            i["node_data"][quarter + "_" + str(scenario_2)]
                            - i["node_data"][quarter + "_" + str(scenario_1)]
                        )
                        / i["node_data"][quarter + "_" + str(scenario_1)]
                    ) * 100, 2)
                cpa_percent.append(i)
        final["cpa"] = cpa_percent
        return final

    def get_scenario_comp_graph(self, request_data):
        scenario_1 = request_data["scenario_1"] or 1
        scenario_2 = request_data["scenario_2"] or 2
        period_type = request_data["period_type"] or "year"
        outcome = request_data["outcome"] or "outcome2"
        nodes_data = request_data["nodes"]
        nodes = [int(i) for i in nodes_data]
        # nodes = request_data["nodes"] or [2003, 2005]
        customer_names = {
            "outcome2": "outcome2",
            "outcome1": "outcome1",
        }
        if outcome == "outcome2":
            outcome = "outcome2"
        elif outcome == "outcome1":
            outcome = "outcome1"
        scenario_name_1_df = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_name(scenario_1)
        )
        scenario_name_1 = scenario_name_1_df.iloc[0][0]

        scenario_name_2_df = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_name(scenario_2)
        )
        scenario_name_2 = scenario_name_2_df.iloc[0][0]
        s1_results = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_graph(
                scenario_1, scenario_2, outcome, period_type
            )
        )
        s1_results["allocation"] = s1_results["allocation"].astype(float)
        s2_results = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_graph(
                scenario_2, scenario_1, outcome, period_type
            )
        )
        s2_results["allocation"] = s2_results["allocation"].astype(float)
        s1_spends = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_details_graph(
                scenario_1, scenario_2, period_type
            )
        )
        s1_spends["spend_value"] = s1_spends["spend_value"].astype(float)
        s2_spends = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_details_graph(
                scenario_2, scenario_1, period_type
            )
        )
        s2_spends["spend_value"] = s2_spends["spend_value"].astype(float)
        # pdb.set_trace()
        if request_data["period_type"] == "quarter":
            s1_results = s1_results[
                s1_results["quarter"] == request_data["quarter1"] + "_" + scenario_1
            ]
            s2_results = s2_results[
                s2_results["quarter"] == request_data["quarter2"] + "_" + scenario_2
            ]
            s1_spends = s1_spends[
                s1_spends["quarter"] == request_data["quarter1"] + "_" + scenario_1
            ]
            s2_spends = s2_spends[
                s2_spends["quarter"] == request_data["quarter2"] + "_" + scenario_2
            ]
        elif request_data["period_type"] == "month":
            s1_results = s1_results[
                s1_results["month"] == request_data["month1"] + "_" + scenario_1
            ]
            s2_results = s2_results[
                s2_results["month"] == request_data["month2"] + "_" + scenario_2
            ]
            s1_spends = s1_spends[
                s1_spends["month"] == request_data["month1"] + "_" + scenario_1
            ]
            s2_spends = s2_spends[
                s2_spends["month"] == request_data["month2"] + "_" + scenario_2
            ]
            
        # results = pd.merge(s1_results, s2_results, how="left", on=["node_name"])
        results = pd.merge(s1_results, s2_results, how="left", on=["node_name"], validate="many_to_many")
        results.rename(
            {"allocation_x": "scenario1", "allocation_y": "scenario2"},
            axis=1,
            inplace=True,
        )

        # media_hierarchy = pd.DataFrame.from_records(self.reporting_dao.get_media_hierarchy_new()).sort_values(
        #     by=['node_seq', 'node_id'])

        ## Fix for not reporting DMA level numbers --- Himanshu -- 05/07/2020
        # In case, we need DMA level reporting, comment this line and
        # comment the above line
        media_hierarchy = pd.DataFrame.from_records(
            self.scenario_comparison_dao.touchpoints()
        ).sort_values(by=["node_seq", "node_id"])

        media_hierarchy["leaf_nodes"] = media_hierarchy["leaf_nodes"].map(eval)

        # self.df = media_hierarchy.merge(results, on=['node_name', 'geo'], how='left').replace(r'^\s*$', np.nan,
        #                                                                                       regex=True)

        ## Fix for not reporting DMA level numbers --- Himanshu -- 05/07/2020
        # In case, we need DMA level reporting, comment this line and
        # comment the above line
        # self.df = media_hierarchy.merge(results, on=["node_name"], how="left").replace(
        #     r"^\s*$", np.nan, regex=True
        # )
        self.df = media_hierarchy.merge(results, on=["node_name"], how="left", validate="many_to_many").replace(
            r"^\s*$", np.nan, regex=True
        )
        self.df = self.df.rename(
            index=str,
            columns={
                "node_display_name": "node_disp_name",
                "parent_node_id": "node_parent",
            },
        )
        self.df = self.df.fillna("").sort_values(
            by=["node_seq", "node_id"], ascending=[True, True]
        )

        final = []
        if not nodes:
            relevant_nodes = media_hierarchy[(media_hierarchy["level"] == "Level 2") & (media_hierarchy["node_id"] < 2040)]["node_id"]
        else:
            relevant_nodes = media_hierarchy[media_hierarchy["node_id"].isin(nodes)]["node_id"]
        for i, node in media_hierarchy[
            media_hierarchy["node_id"].isin(relevant_nodes)
        ].iterrows():
            data = self.df[self.df["node_name"].isin(node.leaf_nodes)].replace(
                "", np.nan
            )
            row_spend = {}
            row_spend["node_id"] = node["node_id"]
            row_spend["node_name"] = node["node_name"]
            row_spend["node_disp_name"] = node["node_display_name"]
            row_spend["Spend " + scenario_name_1] = s1_spends[
                s1_spends["node_name"].isin(node.leaf_nodes)
            ]["spend_value"].sum()
            row_spend["Spend " + scenario_name_2] = s2_spends[
                s2_spends["node_name"].isin(node.leaf_nodes)
            ]["spend_value"].sum()
            row_spend[customer_names[outcome] + " " + scenario_name_1] = data[
                "scenario1"
            ].sum()
            row_spend[customer_names[outcome] + " " + scenario_name_2] = data[
                "scenario2"
            ].sum()
            final.append(row_spend)
        sorted_data = sorted(final, key=lambda x: list(x.values())[4])[::-1]
        return sorted_data

    def fetch_spend_comparison_summary(self, request_data):
        logger.info(
            "Scenario Comparison: summary preparation for comparison is started"
        )
        scenario_1 = int(request_data["scenario_1"]) or 1
        scenario_2 = int(request_data["scenario_2"]) or 2
        period_type = request_data["period_type"] or "year"
        quarter1 = ""
        quarter2 = ""
        if period_type == "quarter":
            quarter1 = request_data["quarter"]
        if period_type == "month":
            d = {
                "Jan": 1,
                "Feb": 2,
                "Mar": 3,
                "Apr": 4,
                "May": 5,
                "Jun": 6,
                "Jul": 7,
                "Aug": 8,
                "Sep": 9,
                "Oct": 10,
                "Nov": 11,
                "Dec": 12,
            }
            quarter1 = d[request_data["month"]]

        include_control = request_data["required_control"]
        result = {}

        scenario_1_name = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_name(scenario_1)
        )
        result["s1_name"] = scenario_1_name.iloc[0][0]
        scenario_2_name = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_name(scenario_2)
        )
        result["s2_name"] = scenario_2_name.iloc[0][0]
        if result["s1_name"] == result["s2_name"]:
            result["s1_name"] = result["s1_name"] + " " + quarter1
            result["s2_name"] = result["s2_name"] + " " + quarter2

        # Summary of spend
        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_total_scenario_spend_details_new(
                scenario_1, scenario_2, period_type, quarter1
            )
        )
        result["s1_spends"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_total_scenario_spend_details_new(
                scenario_2, scenario_1, period_type, quarter1
            )
        )
        result["s2_spends"] = int(query_output.iloc[0][0])

        # Summary of outcomes

        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_total(
                scenario_1,
                scenario_2,
                "outcome2",
                include_control,
                period_type,
                quarter1,
            )
        )
        result["s1_outcome2"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_total(
                scenario_1, scenario_2, "outcome1", include_control, period_type, quarter1
            )
        )
        result["s1_outcome1"] = int(query_output.iloc[0][0])
        # query_output = pd.DataFrame.from_records(
        #     self.scenario_comparison_dao.get_scenario_spend_allocations_total(scenario_1, scenario_2, 'O_NTFHH_CNT',
        #                                                                       include_control, period_type, quarter1))
        # result["s1_O_NTFHH_CNT"] = int(query_output.iloc[0][0])

        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_total(
                scenario_2,
                scenario_1,
                "outcome2",
                include_control,
                period_type,
                quarter1,
            )
        )
        result["s2_outcome2"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_total(
                scenario_2, scenario_1, "outcome1", include_control, period_type, quarter1
            )
        )
        result["s2_outcome1"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_total_cftbs(
                scenario_2,
                scenario_1,
                "outcome2",
                include_control,
                period_type,
                quarter1,
            )
        )
        result["s2_coutcome2"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_total_cftbs(
                scenario_1,
                scenario_2,
                "outcome2",
                include_control,
                period_type,
                quarter1,
            )
        )
        result["s1_coutcome2"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_total_cftbs(
                scenario_2,
                scenario_1,
                "outcome1",
                include_control,
                period_type,
                quarter1,
            )
        )
        result["s2_coutcome1"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_allocations_total_cftbs(
                scenario_1,
                scenario_2,
                "outcome1",
                include_control,
                period_type,
                quarter1,
            )
        )
        result["s1_coutcome1"] = int(query_output.iloc[0][0])
        # query_output = pd.DataFrame.from_records(
        #     self.scenario_comparison_dao.get_scenario_spend_allocations_total(scenario_2, scenario_1, 'O_NTFHH_CNT',
        #                                                                       include_control, period_type, quarter2))
        # result["s2_O_NTFHH_CNT"] = int(query_output.iloc[0][0])
        result["s1_coutcome2"] = (
            round(result["s1_spends"] / result["s1_coutcome2"], 4)
            if result["s1_coutcome2"] != 0
            else 0
        )
        result["s1_coutcome1"] = (
            round(result["s1_spends"] / result["s1_coutcome1"], 4)
            if result["s1_coutcome1"] != 0
            else 0
        )
        result["s2_coutcome1"] = (
            round(result["s2_spends"] / result["s2_coutcome1"], 4)
            if result["s2_coutcome1"] != 0
            else 0
        )
        result["s2_coutcome2"] = (
            round(result["s2_spends"] / result["s2_coutcome2"], 4)
            if result["s2_coutcome2"] != 0
            else 0
        )
        logger.info(
            "Scenario Comparison: summary preparation for comparison is completed"
        )
        return result

    def download_data(self, request_data):
        if request_data:
            scenarios = eval(request_data["scenarios"]) or [1, 2]
            period_type = str(request_data["period_type"])
            if str(request_data["outcome"]) == "Overall-Change":
                customer_list = [
                    "outcome1",
                    "outcome2",
                ]
            elif str(request_data["outcome"]) == "outcome1":
                customer_list = ["outcome1"]
            else:
                customer_list = ["outcome2"]
        else:
            scenarios = [1, 2]
            period_type = "year"
            customer_list = [
                "outcome1",
                "outcome2",
            ]

        # Get media hierarchy
        media_hierarchy = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_media_hierarchy()
        ).sort_values(by=["node_seq", "node_id"])
        # Read database period_master
        # period_master = pd.DataFrame(self.scenario_comparison_dao.get_period_master())

        # Filter period_master data as per period_type
        # period_master_filter = period_master[period_master['period_type'] == period_type].reset_index()
        # period_master_filter = period_master_filter[['period_type', 'period_name_short']]
        def lnc(x):
            if x[0] == 2001:
                s = "["
                a = eval(x[1])
                for i in a:
                    if "_FLAGS_" in i:
                        continue
                    else:
                        s = s + "'" + i + "', "
                s = s + "]"
                return s

            return x[1]

        media_hierarchy["leaf_nodes"] = media_hierarchy[
            ["node_id", "leaf_nodes"]
        ].apply(lnc, axis=1)
        media_hierarchy["check"] = media_hierarchy["leaf_nodes"].apply(
            lambda x: 1 if "_FLAGS_" not in str(x) else 0
        )
        media_hierarchy = media_hierarchy[media_hierarchy["check"] == 1]
        media_hierarchy = media_hierarchy.drop("check", axis=1)
        if len(customer_list) == 1:
            scenario_name = []
            final_allocation_cols = []
            spend_cols = []
            allocation_cols = []
            for index, scenario_id in enumerate(scenarios):
                # Output dataframe
                final = pd.DataFrame()  # Output dataframe

                si_name = self.scenario_comparison_dao.get_scenario_name(scenario_id)[
                    0
                ]["scenario_name"]
                scenario_name.append(si_name)

                customer = customer_list[0]
                ## Get allocations for each customer for individual scenarios for a specific period
                allocation_df_i = pd.DataFrame.from_records(
                    self.scenario_comparison_dao.get_scenario_spend_allocations_download(
                        scenario_id, scenario_id, period_type
                    )
                )
                allocation_df_i.rename(
                    columns={"allocation": "allocation" + "_" + si_name}, inplace=True
                )
                allocation_cols.append("allocation" + "_" + si_name)

                ## Calculate spends for each scenario and period type
                spend_df_i = pd.DataFrame.from_records(
                    self.scenario_comparison_dao.get_scenario_spend_details_download(
                        scenario_id, scenario_id, period_type
                    )
                )
                spend_df_i.rename(
                    columns={"spend_value": "spend_value" + "_" + si_name}, inplace=True
                )
                spend_cols.append("spend_value" + "_" + si_name)

                # Get single dataframe for allocation and spends by merging individual dataframes
                if index == 0:
                    allocation_df = allocation_df_i.copy()
                    spend_df = spend_df_i.copy()
                else:
                    allocation_df = allocation_df.merge(
                        allocation_df_i,
                        on=["outcome", "node_name", "period_name"],
                        how="outer",
                    )
                    spend_df = spend_df.merge(
                        spend_df_i, on=["node_name", "period_name"], how="outer"
                    )
                # allocation_df["node_name"]=allocation_df["node_name"].apply(lambda x: "I_SEO" if x=="I_SEO_SEO" else x)
                # allocation_df["node_name"] = allocation_df["node_name"].apply(lambda x: x.strip())
                # spend_df["node_name"] = spend_df["node_name"].apply(lambda x: x.strip())
                # spend_df["node_name"]=spend_df["node_name"].apply(lambda x: "I_SEO" if x=="I_SEO_SEO" else x)

                # Get allocation column list for final result
                final_allocation_cols.extend([si_name + " : " + customer])

            # Get spend cols for final result
            final_spend_cols = list(map(lambda x: x + " : " + "Spends", scenario_name))

            for j, node in media_hierarchy.iterrows():
                all_outcome_allocation_node_df = allocation_df[
                    allocation_df["node_name"].isin(eval(node.leaf_nodes))
                ]
                spend_node_df = spend_df[
                    spend_df["node_name"].isin(eval(node.leaf_nodes))
                ]
                allocation_node_df = all_outcome_allocation_node_df[
                    all_outcome_allocation_node_df["outcome"] == customer
                ]

                ## Insert rows for different period in a period type
                # Ex. - for period_type='halfyear', it'll run two times and
                # get the relevant data fro that period
                spend_node_data = (
                    spend_node_df.groupby(["period_name"])[spend_cols]
                    .sum()
                    .reset_index()
                )
                allocation_node_data = (
                    allocation_node_df.pivot_table(
                        index="period_name",
                        columns="outcome",
                        values=allocation_cols,
                        aggfunc="sum",
                    )
                    .reset_index()
                    .drop(["period_name"], axis=1)
                )

                node_data = pd.concat([spend_node_data, allocation_node_data], axis=1)
                node_data["node_id"] = node["node_id"]
                final = pd.concat([final, node_data])

            final_df = pd.DataFrame(final).replace([np.inf, -np.inf], np.nan).fillna(0)

            # Sorting final_allocation_cols and final_spend _cols due to automatic sorting while drawing pivot and groupby
            final_spend_cols = sorted(final_spend_cols)
            final_allocation_cols = sorted(final_allocation_cols)
            final_df.columns = (
                ["period_name"] + final_spend_cols + final_allocation_cols + ["node_id"]
            )

        else:
            scenario_name = []
            final_allocation_cols = []
            spend_cols = []
            allocation_cols = []
            for index, scenario_id in enumerate(scenarios):
                final = pd.DataFrame()  # Output dataframe

                si_name = self.scenario_comparison_dao.get_scenario_name(scenario_id)[
                    0
                ]["scenario_name"]
                scenario_name.append(si_name)

                ## Get allocations for each customer for individual scenarios for a specific period
                allocation_df_i = pd.DataFrame.from_records(
                    self.scenario_comparison_dao.get_scenario_spend_allocations_download(
                        scenario_id, scenario_id, period_type
                    )
                )
                allocation_df_i.rename(
                    columns={"allocation": "allocation" + "_" + si_name}, inplace=True
                )
                allocation_cols.append("allocation" + "_" + si_name)

                ## Calculate spends for each scenario and period type
                spend_df_i = pd.DataFrame.from_records(
                    self.scenario_comparison_dao.get_scenario_spend_details_download(
                        scenario_id, scenario_id, period_type
                    )
                )
                spend_df_i.rename(
                    columns={"spend_value": "spend_value" + "_" + si_name}, inplace=True
                )
                spend_cols.append("spend_value" + "_" + si_name)

                # Get single dataframe for allocation and spends by merging individual dataframes
                if index == 0:
                    allocation_df = allocation_df_i.copy()
                    spend_df = spend_df_i.copy()
                else:
                    allocation_df = allocation_df.merge(
                        allocation_df_i,
                        on=["outcome", "node_name", "period_name"],
                        how="outer",
                    )
                    spend_df = spend_df.merge(
                        spend_df_i, on=["node_name", "period_name"], how="outer"
                    )
                # allocation_df["node_name"]=allocation_df["node_name"].apply(lambda x: "I_SEO" if x=="I_SEO_SEO" else x)
                # allocation_df["node_name"] = allocation_df["node_name"].apply(lambda x: x.strip())
                # spend_df["node_name"] = spend_df["node_name"].apply(lambda x: x.strip())
                # spend_df["node_name"]=spend_df["node_name"].apply(lambda x: "I_SEO" if x=="I_SEO_SEO" else x)

                # Get allocation column list for final result
                final_allocation_cols.extend(
                    (si_name + " : " + allocation_df.outcome.unique()).tolist()
                )

            # Get spend cols for final result
            final_spend_cols = list(map(lambda x: x + " : " + "Spends", scenario_name))

            for j, node in media_hierarchy.iterrows():
                allocation_node_df = allocation_df[
                    allocation_df["node_name"].isin(eval(node.leaf_nodes))
                ]
                spend_node_df = spend_df[
                    spend_df["node_name"].isin(eval(node.leaf_nodes))
                ]

                ## Insert rows for different period in a period type
                # Ex. - for period_type='halfyear', it'll run two times and
                # get the relevant data from that period
                spend_node_data = spend_node_df.pivot_table(
                    index="period_name", values=spend_cols, aggfunc="sum"
                ).reset_index()
                allocation_node_data = (
                    allocation_node_df.pivot_table(
                        index="period_name",
                        columns="outcome",
                        values=allocation_cols,
                        aggfunc="sum",
                    )
                    .reset_index()
                    .drop(["period_name"], axis=1)
                )

                node_data = pd.concat([spend_node_data, allocation_node_data], axis=1)
                node_data["node_id"] = node["node_id"]
                final = pd.concat([final, node_data])

            final_df = pd.DataFrame(final).replace([np.inf, -np.inf], np.nan).fillna(0)

            # Sorting final_allocation_cols and final_spend _cols due to automatic sorting while drawing pivot and groupby
            # lexographic_check = final_spend_cols[1].split(':')
            # if lexographic_check[0] in final_spend_cols[0]:
            #     final_spend_cols = sorted(final_spend_cols, reverse=True)
            #     final_allocation_cols = sorted(final_allocation_cols, reverse=True)
            # else:
            final_spend_cols = sorted(final_spend_cols)
            final_allocation_cols = sorted(final_allocation_cols)
            final_df.columns = (
                ["period_name"] + final_spend_cols + final_allocation_cols + ["node_id"]
            )

            ## Changing format of columns
            # For existing and ntf assets, column will contain dollar as a perfix
            # For ntfhh, it will just be a number
            # For spends, dollar will be added as prefix
        final_df = final_df.drop_duplicates()
        if len(customer_list) == 1:
            if customer_list[0] == "outcome1":
                final_df[final_df.columns[1].split(":")[0] + " : coutcome1"] = (
                    final_df[final_df.columns[1]] / final_df[final_df.columns[3]]
                )
                final_df[final_df.columns[2].split(":")[0] + " : coutcome1"] = (
                    final_df[final_df.columns[2]] / final_df[final_df.columns[4]]
                )
            else:
                final_df[final_df.columns[1].split(":")[0] + " : coutcome2"] = (
                    final_df[final_df.columns[1]] / final_df[final_df.columns[3]]
                )
                final_df[final_df.columns[2].split(":")[0] + " : coutcome2"] = (
                    final_df[final_df.columns[2]] / final_df[final_df.columns[4]]
                )
        else:
            final_df[final_df.columns[1].split(":")[0] + " : coutcome1"] = (
                final_df[final_df.columns[1]] / final_df[final_df.columns[3]]
            )
            final_df[final_df.columns[2].split(":")[0] + " : coutcome1"] = (
                final_df[final_df.columns[2]] / final_df[final_df.columns[5]]
            )
            final_df[final_df.columns[1].split(":")[0] + " : coutcome2"] = (
                final_df[final_df.columns[1]] / final_df[final_df.columns[4]]
            )
            final_df[final_df.columns[2].split(":")[0] + " : coutcome2"] = (
                final_df[final_df.columns[2]] / final_df[final_df.columns[6]]
            )
        final_df = final_df.fillna(0)
        final_df = final_df.replace([np.inf, -np.inf], 0)
        c_customers = []
        for i in customer_list:
            if i == "outcome2":
                customer_value = "coutcome2"
            else:
                customer_value = "coutcome1"
            c_customers.append(customer_value)
        for customer in c_customers:
            if customer == "coutcome2" or customer == "coutcome1":
                final_df[
                    final_df.columns[1].split(":")[0] + " : " + customer
                ] = final_df[final_df.columns[1].split(":")[0] + " : " + customer].map(
                    "${:,.0f}".format
                )
                final_df[
                    final_df.columns[2].split(":")[0] + " : " + customer
                ] = final_df[final_df.columns[2].split(":")[0] + " : " + customer].map(
                    "${:,.0f}".format
                )
        for index, scenario_id in enumerate(scenarios):
            si_name = self.scenario_comparison_dao.get_scenario_name(scenario_id)[0][
                "scenario_name"
            ]
            for customer in customer_list:
                if customer in ("outcome2", "outcome1"):
                    final_df[si_name + " : " + customer] = final_df[
                        si_name + " : " + customer
                    ].map("{:,.0f}".format)
                else:
                    final_df[si_name + " : " + customer] = final_df[
                        si_name + " : " + customer
                    ].map("{:,.0f}".format)

            final_df[si_name + " : " + "Spends"] = final_df[
                si_name + " : " + "Spends"
            ].map("${:,.0f}".format)

        full_media_hierarchy = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_media_hierarchy_download_data()
        ).sort_values(by=["node_seq", "node_id"])
        # result = pd.merge(full_media_hierarchy, final_df, how="right", on=["node_id"])
        result = pd.merge(full_media_hierarchy, final_df, how="right", on=["node_id"], validate="many_to_many")
        result.insert(
            2,
            "External Factors/Marketing/Base",
            result["node_id"].apply(
                lambda x: "External Factors"
                if x >= 6000
                else ("Base" if x >= 4000 else "Marketing")
            ),
        )
        result.drop(["node_seq", "node_id"], axis=1, inplace=True)
        result["level"] = result["level"].apply(
            lambda x: "Level 3" if x == "Variable" else x
        )
        result = result.rename(columns={"node_description": "marketing_tactics"})
        if period_type == "month":
            period_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            external_order = ['Marketing', 'Base', 'External Factors']

            # Convert columns to categorical data types with specified order
            result['period_name'] = pd.Categorical(result['period_name'], categories=period_order, ordered=True)
            result[EXTERNAL_FACTORS_MARKETING_BASE] = pd.Categorical(result[EXTERNAL_FACTORS_MARKETING_BASE], categories=external_order, ordered=True)

            # Sort the DataFrame based on the specified order of columns
            result = result.sort_values(by=[EXTERNAL_FACTORS_MARKETING_BASE, 'level', 'marketing_tactics', 'period_name'])            
        return result

    def get_tree_table_headers(self, scenarios, periods):
        """
        Prepare table headers for each metric
        :param scenarios:
        :param periods:
        :return:
        """
        s1 = self.scenario_comparison_dao.get_scenario_name(scenarios[0])
        s2 = self.scenario_comparison_dao.get_scenario_name(scenarios[1])
        headers = []
        for period in periods:
            colsObj1 = {}
            colsObj1["title"] = s1[0]["scenario_name"] + "<br>" + period
            colsObj1["key"] = period + "_" + str(scenarios[0])
            headers.append(colsObj1)
            if scenarios[0] != scenarios[1]:
                colsObj2 = {}
                colsObj2["title"] = s2[0]["scenario_name"] + "<br>" + period
                colsObj2["key"] = period + "_" + str(scenarios[1])
                headers.append(colsObj2)
        colObj3 = {}
        colObj3["title"] = "Change"
        colObj3["key"] = "percent"
        headers.append(colObj3)
        return {
            "outcome1": headers,
            "outcome2": headers,
        }

    def due_to_analysis(self, request_data):
        period_type = request_data["period_type"]
        # year_2 = int(request_data["scenario_1"])
        # year_1 = int(request_data["scenario_2"])
        period_2 = request_data["period_1"]
        period_1 = request_data["period_2"]
        scenario_2 = int(request_data["scenario_1"])
        scenario_1 = int(request_data["scenario_2"])
        if period_type == "month":
            d = {
                "Jan": 1,
                "Feb": 2,
                "Mar": 3,
                "Apr": 4,
                "May": 5,
                "Jun": 6,
                "Jul": 7,
                "Aug": 8,
                "Sep": 9,
                "Oct": 10,
                "Nov": 11,
                "Dec": 12,
            }
            fmt_period_2 = d[request_data["period_1"]]
            fmt_period_1 = d[request_data["period_2"]]
        elif period_type == "year":
            fmt_period_2 = self.scenario_comparison_dao.fetch_year(scenario_2)[0][
                "year"
            ]
            fmt_period_1 = self.scenario_comparison_dao.fetch_year(scenario_1)[0][
                "year"
            ]
        else:
            fmt_period_2 = request_data["period_1"].replace("H", "").replace("Q", "")
            fmt_period_1 = request_data["period_2"].replace("H", "").replace("Q", "")
        year1_name = request_data["year_1"]
        year2_name = request_data["year_2"]
        selected_node = int(request_data["node"])
        customer_list = ["outcome1", "outcome2"]
        customer_names = {
            "outcome2": "outcome2",
            # "O_NTFHH_CNT": "NTF_HH_Count",
            "outcome1": "outcome1",
        }
        media_hierarchy = pd.DataFrame.from_records(
            self.scenario_comparison_dao.touchpoints()
        )
        media_hierarchy["leaf_nodes"] = media_hierarchy["leaf_nodes"].map(eval)
        selected_node_names = media_hierarchy[
            media_hierarchy["node_id"] == selected_node
        ]["leaf_nodes"].reset_index(drop=True)[0]

        chart_data = {}
        for customer in customer_list:
            # Read allocation table
            allocation_period_1 = pd.DataFrame.from_records(
                self.scenario_comparison_dao.fetch_allocation_period(
                    scenario_1, scenario_2, period_type, fmt_period_1, customer
                )
            )
            allocation_period_1["allocation"] = allocation_period_1[
                "allocation"
            ].astype(float)
            allocation_period_2 = pd.DataFrame.from_records(
                self.scenario_comparison_dao.fetch_allocation_period(
                    scenario_2, scenario_1, period_type, fmt_period_2, customer
                )
            )
            allocation_period_2["allocation"] = allocation_period_2[
                "allocation"
            ].astype(float)
            new_spend = pd.DataFrame.from_records(
                self.scenario_comparison_dao.fetch_spends(
                    scenario_1, scenario_2, period_type
                )
            )
            new_spend["spend_value"] = new_spend["spend_value"].astype(float)
            old_spend = pd.DataFrame.from_records(
                self.scenario_comparison_dao.fetch_spends(
                    scenario_2, scenario_1, period_type
                )
            )
            old_spend["spend_value"] = old_spend["spend_value"].astype(float)
            node_data = pd.DataFrame.from_records(
                self.scenario_comparison_dao.fetch_node_data()
            )
            if old_spend["period_name"][1] != "Year":
                old_spend = old_spend[
                    old_spend["period_name"] == request_data["period_2"]
                ]
                new_spend = new_spend[
                    new_spend["period_name"] == request_data["period_1"]
                ]

            # List of touchpoints
            touchpoints = [
                node
                for node in allocation_period_1["node_name"]
                if node.endswith("_SP")
            ]
            # Filter only the relevant touchpoints as per the touchpoint list
            new_spend = new_spend[new_spend["node_name"].isin(touchpoints)]
            new_spend = new_spend.sort_values(by=["node_name"]).reset_index(drop=True)

            old_spend = old_spend[old_spend["node_name"].isin(touchpoints)]
            old_spend = old_spend.sort_values(by=["node_name"]).reset_index(drop=True)

            # Filter only the relevant touchpoints as per the touchpoint list
            allocation_period_1 = allocation_period_1[
                allocation_period_1["node_name"].isin(touchpoints)
            ]
            allocation_period_1 = allocation_period_1.sort_values(
                by=["node_name"]
            ).reset_index(drop=True)

            allocation_period_2 = allocation_period_2[
                allocation_period_2["node_name"].isin(touchpoints)
            ]
            allocation_period_2 = allocation_period_2.sort_values(
                by=["node_name"]
            ).reset_index(drop=True)
            touchpoints = [
                node
                for node in allocation_period_1["node_name"]
                if node.endswith("_SP")
            ]
            # Filter out relevant columns from the dataframe
            allocation_period_1 = allocation_period_1[["allocation"]]
            allocation_period_2 = allocation_period_2[["allocation"]]
            new_spend = new_spend[["spend_value"]]
            old_spend = old_spend[["spend_value"]]

            # Renaming the columns with same column name for series multiplication
            allocation_period_1.columns = ["values"]
            allocation_period_2.columns = ["values"]
            new_spend.columns = ["values"]
            old_spend.columns = ["values"]

            # Calculations as per the paper --------------------------------------------

            """
            modification as per SOC approach: adding a small value to attribution and spend
            since we have to monitor 2 conditions specifically data frame operation results into error
            therefore we need to handle each items for due-to analysis individually
            """

            allocation_period_1 += 1e-7
            allocation_period_2 += 1e-7
            new_spend += 1e-7
            old_spend += 1e-7

            due_to = pd.concat(
                [allocation_period_1, allocation_period_2, new_spend, old_spend], axis=1
            )
            due_to.columns = [
                "Attribution 1",
                "Attribution 2",
                "New Spend",
                "Old Spend",
            ]

            _efficiency_unchanged_attributes = []
            _spend_unchanged_attributes = []
            _spend_touchpoint_attributions = []
            _efficiency_touchpoint_attributions = []

            for items in due_to.iterrows():
                _new_spend = items[1]["New Spend"]
                _old_spend = items[1]["Old Spend"]
                _allocation_period_1 = items[1]["Attribution 1"]
                _allocation_period_2 = items[1]["Attribution 2"]

                _efficiency_unchanged_attribute = _new_spend * (
                    _allocation_period_2 / _old_spend
                )
                _efficiency_unchanged_attributes.append(_efficiency_unchanged_attribute)

                _spend_unchanged_attribute = _old_spend * (
                    _allocation_period_1 / _new_spend
                )
                _spend_unchanged_attributes.append(_spend_unchanged_attribute)

                _allocation_difference = _allocation_period_1 - _allocation_period_2
                _old_allocation_difference = (
                    _efficiency_unchanged_attribute - _allocation_period_2
                )
                _new_allocation_difference = (
                    _spend_unchanged_attribute - _allocation_period_2
                )

                if (_old_spend == 1e-7 and _new_spend != 1e-7) or (
                    _old_spend != 1e-7 and _new_spend == 1e-7
                ):
                    _spend_touchpoint_attribution = _allocation_difference
                    _efficiency_touchpoint_attribution = 0
                else:
                    _spend_touchpoint_attribution = _old_allocation_difference + abs(
                        _old_allocation_difference
                    ) / (
                        abs(_old_allocation_difference)
                        + abs(_new_allocation_difference)
                    ) * (
                        _allocation_difference
                        - (_old_allocation_difference + _new_allocation_difference)
                    )

                    _efficiency_touchpoint_attribution = (
                        _new_allocation_difference
                        + abs(_new_allocation_difference)
                        / (
                            abs(_old_allocation_difference)
                            + abs(_new_allocation_difference)
                        )
                        * (
                            _allocation_difference
                            - (_old_allocation_difference + _new_allocation_difference)
                        )
                    )

                _spend_touchpoint_attributions.append(_spend_touchpoint_attribution)
                _efficiency_touchpoint_attributions.append(
                    _efficiency_touchpoint_attribution
                )

            efficiency_unchanged_attributes = pd.DataFrame(
                _efficiency_unchanged_attributes
            )
            spend_unchanged_attributes = pd.DataFrame(_spend_unchanged_attributes)
            spend_touchpoint_attribution = pd.DataFrame(_spend_touchpoint_attributions)
            efficiency_touchpoint_attribution = pd.DataFrame(
                _efficiency_touchpoint_attributions
            )

            # Output the results in a new dataframe
            result = pd.DataFrame()
            result[period_1 + str(scenario_1)] = allocation_period_1["values"]
            result["Touch_Points"] = touchpoints
            result[SPEND_EFFECT] = spend_touchpoint_attribution
            result[EFFICIENCY_EFFECT] = efficiency_touchpoint_attribution
            result[period_2 + str(scenario_2)] = allocation_period_2["values"]
            result = pd.merge(
                result,
                node_data,
                left_on="Touch_Points",
                right_on="node_name",
                how="left",
                validate=None
            )
            if len(selected_node_names) > 0:
                result = result[result["node_name"].isin(selected_node_names)]
            else:
                result = result

            result.drop(
                ["Touch_Points", "node_display_name", "node_name"], axis=1, inplace=True
            )

            data = result

            if period_type == "year":
                axis_label_start = year1_name + "-Year"
                axis_label_end = year2_name + "-Year"
            else:
                axis_label_start = year1_name + "-" + period_2
                axis_label_end = year2_name + "-" + period_1

            waterfall_chart_data = getWaterfallChartData(
                base={
                    "name": axis_label_start,
                    "value": data[period_2 + str(scenario_2)].sum(),
                },
                incremental={
                    "names": [SPEND_EFFECT, EFFICIENCY_EFFECT],
                    "values": [
                        data[SPEND_EFFECT].sum(),
                        data[EFFICIENCY_EFFECT].sum(),
                    ],
                },
                total={
                    "name": axis_label_end,
                    "value": data[period_1 + str(scenario_1)].sum(),
                },
                start_point=0,
                add_gap=False,
                round_digits=4,
            )
            chart_data[customer_names[customer]] = waterfall_chart_data

        return chart_data

    def fetch_data_ROMI_CPA(self, request):
        logger.info("Reporting: data preparation for ROMI and CPA is started")
        from_year = scenario1 = int(request["scenario_1"])
        to_year = scenario2 = int(request["scenario_2"])
        from_quarter = request["from_quarter"]
        to_quarter = request["to_quarter"]
        d = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
        }
        from_month = d[request["from_month"]]
        to_month = d[request["to_month"]]
        period_type = request["period_type"]
        nodes = request.get("nodes", [])
        if len(nodes) > 0:
            nodes = [int(i) for i in nodes]
        final = {
            "year": [],
            "halfyear": [],
            "quarter": [],
            "year_labels": [],
            "quarter_labels": [],
            "halfyear_labels": [],
            "month": [],
            "month_labels": []
            # "existing_ntf_assets": [],
            # "ntf_assets": [],
            # "cpa": [],
        }
        # get the allocations for the year
        allocation_df1 = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_allocations_for_cpa_romi(scenario1)
        )
        allocation_df2 = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_allocations_for_cpa_romi(scenario2)
        )

        allocation_df = pd.concat([allocation_df1, allocation_df2], axis=0)
        allocation_df = allocation_df.reset_index().drop("index", axis=1)
        allocation_df.rename(columns={"scenario_id": "year"}, inplace=True)
        allocation_df["value"] = allocation_df["value"].astype(float)
        if not allocation_df.empty:
            query_result_wide = pd.pivot_table(
                allocation_df,
                values="value",
                index=["node_name", "year", "halfyear", "quarter", "month"],
                columns="outcome",
            )
        else:
            return final
        # get the spends for the year
        spend1 = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_romi_cpa(from_year)
        )
        spend2 = pd.DataFrame.from_records(
            self.scenario_comparison_dao.get_scenario_spend_romi_cpa(to_year)
        )

        spend = pd.concat([spend1, spend2], axis=0)
        spend = spend.reset_index().drop("index", axis=1)
        spend.rename(columns={"scenario_id": "year"}, inplace=True)
        spend["spend_value"] = spend["spend_value"].astype(float)
        # data = query_result_wide.merge(
        #     spend, on=["node_name", "year", "halfyear", "quarter", "month"], how="left"
        # ).fillna(0)
        data = query_result_wide.merge(
            spend, on=["node_name", "year", "halfyear", "quarter", "month"], how="left"
        , validate="many_to_many").fillna(0)
        media_hierarchy = pd.DataFrame.from_records(
            self.scenario_comparison_dao.touchpoints()
        ).sort_values(by=["node_seq", "node_id"])

        # get the media nodes from media hierarchy table data frame
        if len(nodes) == 0:
            media_leaf_nodes = media_hierarchy[media_hierarchy["node_id"] == 2001][
                "leaf_nodes"
            ].iloc[0]
            media_data = data[data["node_name"].isin(eval(media_leaf_nodes))]
        else:
            media_leaf_nodes = media_hierarchy[media_hierarchy["node_id"].isin(nodes)][
                "leaf_nodes"
            ].iloc[0]
            leaf_nodes = eval(media_leaf_nodes)
            media_data = data[data["node_name"].isin(leaf_nodes)]
        media_data["outcome1"] = media_data["outcome1"].fillna(0)
        media_data["spend_value"] = media_data["spend_value"].fillna(0)
        # media_data["O_NTFHH_CNT"] = media_data["O_NTFHH_CNT"].fillna(0)

        # media_data = pd.merge(media_data, media_hierarchy)
        media_data = pd.merge(media_data, media_hierarchy, how="inner", on=None, validate="many_to_many")

        no_of_years = to_year - from_year + 1
        # iterate for number of given years between from and to years
        for year in [from_year, to_year]:
            current_year = year
            row = {}
            #  get the total year data for each year
            if period_type == "year":
                data = media_data[media_data.year.eq(current_year)].sum()
                row["coutcome1"] = data["outcome1"] / data["spend_value"]
                row["csu"] = data["outcome2"] / data["spend_value"]
                # row["cpa"] = data["spend_value"] / data["O_NTFHH_CNT"]
                row["year"] = current_year
                row["spend"] = data["spend_value"]
                row["total_assets"] = row["coutcome1"] + row["csu"]
                if data["spend_value"] == 0.0:
                    row["coutcome1"] = 0
                    row["csu"] = 0
                    row["total_assets"] = 0
                    # row["cpa"] = 0
                final["year"].append(row)
                final["year_labels"].append(row["year"])

            elif period_type == "quarter":
                d = {from_year: from_quarter, to_year: to_quarter}
                # group the data by quarter for each year
                data = (
                    media_data[media_data.year.eq(current_year)]
                    .groupby(by="quarter", as_index=False)
                    .sum()
                )
                for quarter_index in [int(d[current_year].replace("Q", ""))]:
                    row = {}
                    individual_quarter_data = data.iloc[quarter_index - 1]

                    # if from_year and to_year are same, then get the quarter data for same year
                    if from_year != to_year:
                        if current_year != 0:
                            row["coutcome1"] = round(
                                individual_quarter_data["outcome1"]
                                / individual_quarter_data["spend_value"],
                                4,
                            )
                            row["csu"] = round(
                                individual_quarter_data["outcome2"]
                                / individual_quarter_data["spend_value"],
                                4,
                            )
                            # row["cpa"] = round(
                            #     individual_quarter_data["spend_value"]
                            #     / individual_quarter_data["O_NTFHH_CNT"],
                            #     4,
                            # )
                            row["year"] = current_year
                            row["spend"] = individual_quarter_data["spend_value"]
                            row["quarter"] = individual_quarter_data["quarter"]
                            row["total_assets"] = row["coutcome1"] + row["csu"]

                            if individual_quarter_data["spend_value"] == 0.0:
                                row["coutcome1"] = 0
                                row["csu"] = 0
                                row["total_assets"] = 0
                                # row["cpa"] = 0
                            final["quarter"].append(row)
                            final["quarter_labels"].append(
                                "Q"
                                + str(int(row["quarter"]))
                                + "'"
                                + str(current_year)[2:]
                            )  # Q1'2018

                    # if from_year and to_year are different, get the quarter data for all the given years between from and to quarters
                    else:
                        if (
                            (current_year != 0 and quarter_index + 1 >= from_quarter)
                            or (current_year != from_year and current_year != to_year)
                            or (
                                current_year != to_year
                                and quarter_index + 1 <= to_quarter
                            )
                        ):
                            row["coutcome1"] = round(
                                individual_quarter_data["outcome1"]
                                / individual_quarter_data["spend_value"],
                                4,
                            )
                            row["csu"] = round(
                                individual_quarter_data["outcome2"]
                                / individual_quarter_data["spend_value"],
                                4,
                            )
                            # row["cpa"] = round(
                            #     individual_quarter_data["spend_value"]
                            #     / individual_quarter_data["O_NTFHH_CNT"],
                            #     4,
                            # )
                            row["year"] = current_year
                            row["spend"] = individual_quarter_data["spend_value"]
                            row["quarter"] = individual_quarter_data["quarter"]
                            row["total_assets"] = row["csu"] + row["coutcome1"]

                            if individual_quarter_data["spend_value"] == 0.0:
                                row["csu"] = 0
                                row["coutcome1"] = 0
                                row["total_assets"] = 0
                                row["cpa"] = 0
                            final["quarter"].append(row)
                            final["quarter_labels"].append(
                                "Q"
                                + str(int(row["quarter"]))
                                + "'"
                                + str(current_year)[2:]
                            )  # Q1'2018

            elif period_type == "month":
                d = {from_year: from_month, to_year: to_month}
                # group the data by month for each year
                data = (
                    media_data[media_data.year.eq(current_year)]
                    .groupby(by="month", as_index=False)
                    .sum()
                )
                monthly = {
                    1: "Jan",
                    2: "Feb",
                    3: "Mar",
                    4: "Apr",
                    5: "May",
                    6: "Jun",
                    7: "Jul",
                    8: "Aug",
                    9: "Sep",
                    10: "Oct",
                    11: "Nov",
                    12: "Dec",
                }
                for monthly_index in [d[current_year]]:
                    row = {}
                    individual_month_data = data.iloc[monthly_index - 1]
                    # if from_year and to_year are same, then get the month data for same year
                    if (from_year != to_year) or (from_year == to_year):
                        if current_year != 0:
                            row["coutcome1"] = round(
                                individual_month_data["outcome1"]
                                / individual_month_data["spend_value"],
                                4,
                            )
                            row["csu"] = round(
                                individual_month_data["outcome2"]
                                / individual_month_data["spend_value"],
                                4,
                            )
                            # row["cpa"] = round(
                            #     individual_month_data["spend_value"]
                            #     / individual_month_data["O_NTFHH_CNT"],
                            #     4,
                            # )
                            row["year"] = current_year
                            row["spend"] = individual_month_data["spend_value"]
                            row["month"] = individual_month_data["month"]
                            row["total_assets"] = row["coutcome1"] + row["csu"]

                            if individual_month_data["spend_value"] == 0.0:
                                row["coutcome1"] = 0
                                row["csu"] = 0
                                row["total_assets"] = 0
                                # row["cpa"] = 0
                            final["month"].append(row)
                            final["month_labels"].append(
                                monthly[int(row["month"])] + "'" + str(current_year)[2:]
                            )  # Q1'2018

        logger.info("Reporting: data preparation for ROMI and CPA is completed")
        return final
