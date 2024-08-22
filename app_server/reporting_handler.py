"""
This module is for handling reporting
"""
import io
import json
import time

import numpy as np
import pandas as pd

from app_server.custom_logger import get_logger
from app_server.database_handler import DatabaseHandler
from app_server.reporting_dao import ReportingDAO
from app_server.WaterfallChart import getWaterfallChartData

logger = get_logger(__name__)

LEVEL_1 = "Level 1"
LEVEL_2 = "Level 2"
LEVEL_3 = "Level 3"
FORMAL_STRING = r"^\s*$"
FORMAT_STRING = "{:,.0f}"
SPEND = "Spend "
SPENDS = " Spends"
SPEND_EFFECT = "Spend Effect"
EFFICIENCY_EFFECT = "Efficiency Effect"
CURRENCY_FORMAT = "${:,.0f}"
PERCENTAGE_FORMAT = "{:,.5f}%"
DECIMAL_FORMAT = "{:,.5f}"

class ReportingHandler(object):
    def __init__(self):
        self.db_conn = DatabaseHandler().get_database_conn()
        self.reporting_dao = ReportingDAO(self.db_conn)
        self.df = pd.DataFrame()

    def ParentNodeAggegation(self, node, d, col):
        # print("ParentNodeAgg",node,d,col,len(self.df[(self.df['node_id'] == node)]['parent_node_id']))
        if self.df[(self.df["node_id"] == node)][col].isna().sum() > 0:
            self.df.loc[(self.df["node_id"] == node), col] = 0

        self.df.loc[(self.df["node_id"] == node), col] = (
            self.df.loc[(self.df["node_id"] == node), col] + d
        )

        if len(self.df[(self.df["node_id"] == node)]["parent_node_id"]) > 0:
            # print("cond1", node, self.df[(self.df['node_id'] == node)]['parent_node_id'].iloc[0])
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

    def Parentnodechange(
        self, node, col
    ):  # for a given node&period_name changes Parent node value
        # print("pnc", node, col, self.df[self.df['parent_node_id'] == node][col].isna().sum())
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
            # print("nodes :", nodes)
            for node in nodes:
                self.Parentnodechange(node, col)
            return self.df

    def fetch_yearlist_from_reporting(self):
        """
        Method to fetch list of years from reporting allocation table
        :return:years = [{},{}]
        """
        try:
            year_list = self.reporting_dao.get_reporting_allocations_years()
            return year_list
        except Exception as e:
            logger.exception("Exception in method fetch_user_scenario %s", str(e))
    def fetch_period_data_reporting_sc(self):
        """
        Method to fetch list of years from secondary contribution table
        :return:years = [{},{}]
        """
        try:
            year_list = pd.DataFrame.from_records(self.reporting_dao.get_reporting_sc_module())
            distinct_years = year_list['year'].unique()
            results = {}
            results["years"]= {str(year): int(year)for year in distinct_years}
            tatics = year_list['channel_tactic'].unique()
            results["tactics"] = {index: tactic for index, tactic in enumerate(tatics)}
            return results
        except Exception as e:
            logger.exception("Exception in method %s", str(e))
    
    def fetch_data_reporting_sc(self,request_data):
        """
        Method to fetch data from secondary contribution table
        :return:years = [{},{}]
        """
        try:
            selected_tactic = request_data["tatics"]
            outcome = request_data["outcome"]
            if outcome == "outcome1":
                outcome = "outcome1"
            else:
                outcome = "outcome2"
            period = int(request_data["period"])
            data_list = pd.DataFrame.from_records(self.reporting_dao.get_reporting_sc_module())
            # Filter the DataFrame based on the selected tactic
            filtered_df = data_list[(data_list['channel_tactic'] == selected_tactic) &(data_list['year'] == period) &
                          (data_list['metric'] == outcome)].copy()
            filtered_df = filtered_df.drop(['year','metric'], axis=1)
            # Determine percentage columns dynamically
            percentage_columns = [col for col in filtered_df.columns if col not in ['channel_tactic', 'year']]
            # Convert percentage columns to numeric values for plotting
            filtered_df[percentage_columns] = filtered_df[percentage_columns].replace('%', '', regex=True).astype(float)
            chart_data = {
                'categories': list(filtered_df.columns),
                'values': filtered_df.values.tolist()[0]
            }

            return chart_data
        except Exception as e:
            logger.exception("Exception in method %s", str(e))

    def fetch_reporting_allocations(self, request):
        starttime = time.time()
        logger.info("Reporting: data preparation for allocation is started")
        allocation_year = int(request["allocation_year"])
        period_type = request["period_type"]
        quarter = int(request["quarter"])
        month = int(request["month"])
        level = request["level"]
        nodes = request.get("nodes", [])
        final = {"allocation": [], "attribution": [], "efficiency": [], "metric": []}

        allocation_df = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_allocations(
                allocation_year, period_type, quarter, month
            )
        )
        allocation_df["value"] = allocation_df["value"].astype(float)
        # print(allocation_df)
        if not allocation_df.empty:
            query_result_wide = pd.pivot_table(
                allocation_df,
                values="value",
                index=["node_name", "geo"],
                columns="outcome",
            )
        else:
            return final
        spend = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend(
                allocation_year, period_type, quarter, month
            )
        )
        spend["spend_value"] = spend["spend_value"].astype(float)
        data = query_result_wide.merge(
            spend, on=["node_name", "geo"], how="left"
        , validate="many_to_many").fillna(0)

        # media_hierarchy = pd.DataFrame.from_records(self.reporting_dao.get_media_hierarchy_new()).sort_values(
        #     by=['node_seq', 'node_id'])

        ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
        # In case, we need DMA level reporting, comment this line and
        # uncomment the above lines
        media_hierarchy = pd.DataFrame.from_records(
            self.reporting_dao.touchpoints()
        ).sort_values(by=["node_seq", "node_id"])

        # print(media_hierarchy)
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
        control_base_leaf_nodes = media_hierarchy[media_hierarchy["node_id"] == 6000][
            "leaf_nodes"
        ].iloc[0]
        base_leaf_nodes = media_hierarchy[media_hierarchy["node_id"] == 4000][
            "leaf_nodes"
        ].iloc[0]
        media_leaf_nodes = media_hierarchy[media_hierarchy["node_id"] == 2001][
            "leaf_nodes"
        ].iloc[0]
        control_base_data = data[data["node_name"].isin(eval(control_base_leaf_nodes))]
        total_ext_ai_control_base_data = control_base_data["outcome1"].sum()
        total_ntf_asset_control_base_data = control_base_data["outcome2"].sum()
        total_total_asset_control_base_data = (
            total_ext_ai_control_base_data + total_ntf_asset_control_base_data
        )
        total_spend_control_base_data = control_base_data["spend_value"].sum()
        base_data = data[data["node_name"].isin(eval(base_leaf_nodes))]
        total_ext_ai_base_data = base_data["outcome1"].sum()
        total_ntf_asset_base_data = base_data["outcome2"].sum()
        total_total_asset_base_data = total_ext_ai_base_data + total_ntf_asset_base_data
        total_spend_base_data = base_data["spend_value"].sum()

        media_data = data[data["node_name"].isin(eval(media_leaf_nodes))]

        total_ext_ai_media_data = media_data["outcome1"].sum()
        # total_ntf_hh_media_data = media_data["O_NTFHH_CNT"].sum()
        total_ntf_asset_media_data = media_data["outcome2"].sum()
        total_total_asset_media_data = (
            total_ext_ai_media_data + total_ntf_asset_media_data
        )
        total_spend_media_data = media_data["spend_value"].sum()

        # check for the level and filter the media hierarchy data accordingly
        if level == LEVEL_1:
            filtered_media_hierarchy = media_hierarchy[
                media_hierarchy["level"].isin([LEVEL_1])
            ]
        elif level == LEVEL_2:
            filtered_media_hierarchy = media_hierarchy[
                media_hierarchy["level"].isin([LEVEL_1, LEVEL_2])
            ]
        elif level == LEVEL_3:
            filtered_media_hierarchy = media_hierarchy[
                media_hierarchy["level"].isin(
                    [
                        LEVEL_1,
                        LEVEL_2,
                        "Variable",
                    ]
                )
            ]
        elif level == "Level 4":
            filtered_media_hierarchy = media_hierarchy[
                media_hierarchy["level"].isin(
                    [
                        LEVEL_1,
                        LEVEL_2,
                        LEVEL_3,
                        "Variable",
                    ]
                )
            ]

        for i, node in filtered_media_hierarchy.iterrows():
            filtered_df = data[data["node_name"].isin(eval(node.leaf_nodes))]

            row = {}
            row["node_id"] = node["node_id"]
            row["node_name"] = node["node_name"]
            row["node_disp_name"] = node["node_display_name"]
            row["node_parent"] = node["parent_node_id"]
            row["node_seq"] = node["node_seq"]
            row["outcome2"] = round(filtered_df["outcome2"].sum(), 4)
            # row["ntf_hh"] = round(filtered_df["O_NTFHH_CNT"].sum(), 4)
            row["outcome1"] = round(filtered_df["outcome1"].sum(), 4)
            row["total_assets"] = row["outcome2"] + row["outcome1"]
            row["spend_value"] = round(filtered_df["spend_value"].sum(), 4)
            final["allocation"].append(row)

            attr = {}
            attr["node_id"] = node["node_id"]
            attr["node_name"] = node["node_name"]
            attr["node_disp_name"] = node["node_display_name"]
            attr["node_parent"] = node["parent_node_id"]
            attr["node_seq"] = node["node_seq"]

            eff = {}
            eff["node_id"] = node["node_id"]
            eff["node_name"] = node["node_name"]
            eff["node_disp_name"] = node["node_display_name"]
            eff["node_parent"] = node["parent_node_id"]
            eff["node_seq"] = node["node_seq"]

            roi = {}
            roi["node_id"] = node["node_id"]
            roi["node_name"] = node["node_name"]
            roi["node_disp_name"] = node["node_display_name"]
            roi["node_parent"] = node["parent_node_id"]
            roi["node_seq"] = node["node_seq"]
            if node["node_id"] >= 6000:
                attr["outcome2"] = round(
                    row["outcome2"]
                    / (
                        total_ntf_asset_control_base_data
                        + total_ntf_asset_base_data
                        + total_ntf_asset_media_data
                    )
                    * 100,
                    4,
                )
                # attr["ntf_hh"] = round(
                #     row["ntf_hh"] / total_ntf_hh_control_base_data * 100, 4
                # )
                attr["outcome1"] = round(
                    row["outcome1"]
                    / (
                        total_ext_ai_control_base_data
                        + total_ext_ai_base_data
                        + total_ext_ai_media_data
                    )
                    * 100,
                    4,
                )
                attr["total_assets"] = round(
                    row["total_assets"] / total_total_asset_control_base_data * 100, 4
                )
                attr["spend_value"] = round(
                    row["spend_value"] / total_spend_control_base_data * 100, 4
                )
            elif (node["node_id"] >= 4000) and (node["node_id"] < 6000):
                attr["outcome2"] = round(
                    row["outcome2"]
                    / (
                        total_ntf_asset_control_base_data
                        + total_ntf_asset_base_data
                        + total_ntf_asset_media_data
                    )
                    * 100,
                    4,
                )
                # attr["ntf_hh"] = round(
                #     row["ntf_hh"] / total_ntf_hh_control_base_data * 100, 4
                # )
                attr["outcome1"] = round(
                    row["outcome1"]
                    / (
                        total_ext_ai_control_base_data
                        + total_ext_ai_base_data
                        + total_ext_ai_media_data
                    )
                    * 100,
                    4,
                )
                attr["total_assets"] = round(
                    row["total_assets"] / total_total_asset_base_data * 100, 4
                )
                attr["spend_value"] = round(
                    row["spend_value"] / total_spend_base_data * 100, 4
                )

            else:
                attr["outcome2"] = round(
                    row["outcome2"]
                    / (
                        total_ntf_asset_control_base_data
                        + total_ntf_asset_base_data
                        + total_ntf_asset_media_data
                    )
                    * 100,
                    4,
                )
                # attr["ntf_hh"] = round(row["ntf_hh"] / total_ntf_hh_media_data * 100, 4)
                attr["outcome1"] = round(
                    row["outcome1"]
                    / (
                        total_ext_ai_control_base_data
                        + total_ext_ai_base_data
                        + total_ext_ai_media_data
                    )
                    * 100,
                    4,
                )
                attr["total_assets"] = round(
                    row["total_assets"] / total_total_asset_media_data * 100, 4
                )
                attr["spend_value"] = round(
                    row["spend_value"] / total_spend_media_data * 100, 4
                )

            eff["outcome2"] = round(attr["outcome2"] / attr["spend_value"] * 100, 4) / 100
            # eff["ntf_hh"] = round(attr["ntf_hh"] / attr["spend_value"] * 100, 4) / 100
            eff["outcome1"] = round(attr["outcome1"] / attr["spend_value"] * 100, 4) / 100
            eff["total_assets"] = (
                round(attr["total_assets"] / attr["spend_value"] * 100, 4) / 100
            )
            eff["spend_value"] = (
                round(attr["spend_value"] / attr["spend_value"] * 100, 4) / 100
            )

            roi["outcome2"] = round(row["spend_value"] / row["outcome2"], 4)
            roi["outcome1"] = round(row["spend_value"] / row["outcome1"], 4)
            roi["total_assets"] = round(row["total_assets"] / row["spend_value"], 4)
            # roi["ntf_hh"] = round(row["spend_value"] / row["ntf_hh"], 4)

            final["efficiency"].append(eff)
            final["attribution"].append(attr)
            final["metric"].append(roi)
        def spend_sort(json):
            try:
                return float(json['spend_value'])
            except KeyError:
                return 0
        dObjects = {}
        dIndex ={}
        for i in final["allocation"]:
            if i["node_name"]!="0" and i["node_name"]!=None:
                if i["node_parent"] not in dObjects.keys():
                    dObjects[i["node_parent"]] = [i]
                    dIndex[i["node_parent"]] = [final["allocation"].index(i)]
                else:
                    dObjects[i["node_parent"]].append(i)
                    dIndex[i["node_parent"]].append(final["allocation"].index(i))
                
        for key in dObjects.keys():
            spend_sorted = dObjects[key]
            spend_sorted.sort(key=spend_sort, reverse=True)
            dObjects[key] = spend_sorted
            i = 0
            for j in dIndex[key]:
                final["allocation"][j] = spend_sorted[i]
                i+=1
        allocation = (
            pd.DataFrame.from_records(final["allocation"]).fillna("0").drop_duplicates()
        )
        attribution = (
            pd.DataFrame.from_records(final["attribution"])
            .replace([np.inf, -np.inf], np.nan)
            .fillna("0")
            .drop_duplicates()
        )
        efficiency = (
            pd.DataFrame.from_records(final["efficiency"])
            .replace([np.inf, -np.inf], np.nan)
            .fillna("0")
            .drop_duplicates()
        )
        metric = (
            pd.DataFrame.from_records(final["metric"])
            .replace([np.inf, -np.inf], np.nan)
            .fillna("0")
            .drop_duplicates()
        )
        if nodes:
            selectnode_int = [int(node) for node in nodes]
            allocation_node = allocation[allocation["node_id"].isin(selectnode_int)]
            attribution_node = attribution[attribution["node_id"].isin(selectnode_int)]
            efficiency_node = efficiency[efficiency["node_id"].isin(selectnode_int)]
            metric_node = metric[metric["node_id"].isin(selectnode_int)]
            output = {}
            output.update(
                {
                    "allocation": allocation_node.to_dict("records"),
                    "attribution": attribution_node.to_dict("records"),
                    "efficiency": efficiency_node.to_dict("records"),
                    "metric": metric_node.to_dict("records"),
                }
            )
            endtime = time.time()
            logger.info(
                "Reporting: data preparation for allocation is completed in %s",
                (endtime - starttime),
            )
            return output
        else:
            output = {}
            output.update(
                {
                    "allocation": allocation.to_dict("records"),
                    "attribution": attribution.to_dict("records"),
                    "efficiency": efficiency.to_dict("records"),
                    "metric": metric.to_dict("records"),
                }
            )
            endtime = time.time()
            logger.info(
                "Reporting: data preparation for allocation is completed in %s",
                (endtime - starttime),
            )
            return output

    def fetch_reporting_allocation_graph(self, request_data):
        logger.info("Reporting: data preparation for allocation is started")
        allocation_year = int(request_data["allocation_year"])
        period_type = request_data["period_type"]
        quarter = request_data["quarter"]
        month = int(request_data["month"])
        level = request_data["level"]
        month_number_to_name = {
            1: "Jan",
            2: "Feb",
            3: "March",
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
        if level == LEVEL_1:
            nodes_data = [2001, 4000, 6000]
        else:
            nodes_param = request_data.get("nodes")
            nodes_data = nodes_param.split(",") if nodes_param else [2003, 2005]
        nodes = [int(i) for i in nodes_data]
        # nodes = request_data["nodes"] or [2003, 2005]
        customer_names = {
            "outcome2": "outcome2",
            "outcome1": "outcome1",
        }
        # scenario_name_1_df = pd.DataFrame.from_records(
        #     self.reporting_dao.get_scenario_name(allocation_year)
        # )
        # pdb.set_trace()
        # scenario_name_1 = scenario_name_1_df.iloc[0][0]

        # scenario_name_2_df = pd.DataFrame.from_records(
        #     self.reporting_dao.get_scenario_name(allocation_year)
        # )
        # scenario_name_2 = scenario_name_2_df.iloc[0][0]
        s1_results = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_allocations(
                allocation_year, period_type, quarter, month
            )
        )
        s1_results["value"] = s1_results["value"].astype(float)
        s1_spends = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend(
                allocation_year, period_type, quarter, month
            )
        )
        # pdb.set_trace()
        s1_spends["spend_value"] = s1_spends["spend_value"].astype(float)
        # if request_data["period_type"] == "quarter":
        #     s1_results = s1_results[
        #         s1_results["quarter"] == request_data["quarter1"] + "_" + allocation_year
        #     ]
        #     s1_spends = s1_spends[
        #         s1_spends["quarter"] == request_data["quarter1"] + "_" + allocation_year
        #     ]
        # elif request_data["period_type"] == "halfyear":
        #     s1_results = s1_results[
        #         s1_results["halfyear"] == request_data["halfyear1"] + "_" + allocation_year
        #     ]
        #     s1_spends = s1_spends[
        #         s1_spends["halfyear"] == request_data["halfyear1"] + "_" + allocation_year
        #     ]

        results = s1_results
        # results.rename(
        #     {"allocation_x": "scenario1", "allocation_y": "scenario2"},
        #     axis=1,
        #     inplace=True,
        # )

        # media_hierarchy = pd.DataFrame.from_records(self.reporting_dao.get_media_hierarchy_new()).sort_values(
        #     by=['node_seq', 'node_id'])

        ## Fix for not reporting DMA level numbers --- Himanshu -- 05/07/2020
        # In case, we need DMA level reporting, comment this line and
        # comment the above line
        media_hierarchy = pd.DataFrame.from_records(
            self.reporting_dao.touchpoints()
        ).sort_values(by=["node_seq", "node_id"])

        media_hierarchy["leaf_nodes"] = media_hierarchy["leaf_nodes"].map(eval)

        # self.df = media_hierarchy.merge(results, on=['node_name', 'geo'], how='left').replace(r'^\s*$', np.nan,
        #                                                                                       regex=True)

        ## Fix for not reporting DMA level numbers --- Himanshu -- 05/07/2020
        # In case, we need DMA level reporting, comment this line and
        # comment the above line
        # pdb.set_trace()
        # self.df = media_hierarchy.merge(results, on=["node_name"], how="left").replace(
        #     FORMAL_STRING, np.nan, regex=True
        # )
        self.df = media_hierarchy.merge(results, on=["node_name"], how="left", validate="many_to_many").replace(
            FORMAL_STRING, np.nan, regex=True
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
        # pdb.set_trace()
        for i, node in media_hierarchy[
            media_hierarchy["node_id"].isin(nodes)
        ].iterrows():
            data = self.df[self.df["node_name"].isin(node.leaf_nodes)].replace(
                "", np.nan
            )
            # pdb.set_trace()
            row_spend = {}
            row_spend["node_id"] = node["node_id"]
            row_spend["node_name"] = node["node_name"]
            row_spend["node_disp_name"] = node["node_display_name"]
            if period_type == "quarter":
                row_spend[
                    SPEND + str(allocation_year) + " Q" + str(quarter)
                ] = s1_spends[s1_spends["node_name"].isin(node.leaf_nodes)][
                    "spend_value"
                ].sum()
                row_spend[
                    customer_names["outcome2"]
                    + " "
                    + str(allocation_year)
                    + " Q"
                    + str(quarter)
                ] = data[data["outcome"] == "outcome2"]["value"].sum()
                row_spend[
                    customer_names["outcome1"]
                    + " "
                    + str(allocation_year)
                    + " Q"
                    + str(quarter)
                ] = data[data["outcome"] == "outcome1"]["value"].sum()
            elif period_type == "month":
                row_spend[
                    SPEND
                    + str(allocation_year)
                    + " "
                    + str(month_number_to_name[month])
                ] = s1_spends[s1_spends["node_name"].isin(node.leaf_nodes)][
                    "spend_value"
                ].sum()
                row_spend[
                    customer_names["outcome2"]
                    + " "
                    + str(allocation_year)
                    + " "
                    + str(month_number_to_name[month])
                ] = data[data["outcome"] == "outcome2"]["value"].sum()
                row_spend[
                    customer_names["outcome1"]
                    + " "
                    + str(allocation_year)
                    + " "
                    + str(month_number_to_name[month])
                ] = data[data["outcome"] == "outcome1"]["value"].sum()
            else:
                row_spend[SPEND + str(allocation_year)] = s1_spends[
                    s1_spends["node_name"].isin(node.leaf_nodes)
                ]["spend_value"].sum()
                row_spend[customer_names["outcome2"] + " " + str(allocation_year)] = data[
                    data["outcome"] == "outcome2"
                ]["value"].sum()
                row_spend[customer_names["outcome1"] + " " + str(allocation_year)] = data[
                    data["outcome"] == "outcome1"
                ]["value"].sum()
            # pdb.set_trace()
            final.append(row_spend)
        sorted_data = sorted(final, key=lambda x: list(x.values())[3])[::-1]
        return sorted_data

    def fetch_media_hierarchy(self):
        media_hierarchy = pd.DataFrame.from_records(self.reporting_dao.touchpoints())

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
        return media_hierarchy.to_dict(orient="records")

    def fetch_media_hierarchy_level(self, request_data):
        level = request_data["level"]
        media_hierarchy = pd.DataFrame.from_records(self.reporting_dao.touchpoints())

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
        if level == LEVEL_1:
            filtered_media_hierarchy = media_hierarchy[
                media_hierarchy["level"].isin([LEVEL_1])
            ]
        elif level == LEVEL_2:
            filtered_media_hierarchy = media_hierarchy[
                media_hierarchy["level"].isin([LEVEL_1, LEVEL_2])
            ]
        elif level == LEVEL_3:
            filtered_media_hierarchy = media_hierarchy[
                media_hierarchy["level"].isin(
                    [
                        LEVEL_1,
                        LEVEL_2,
                        "Variable",
                    ]
                )
            ]
        return filtered_media_hierarchy.to_json(orient="records")

    def fetch_scenario_list_for_mrc(self):
        return self.reporting_dao.get_scenario_list_for_mrc()

    def fetch_marginal_return_curves_data(self, request_data):
        nodes = request_data["nodes"]
        nodes1 =request_data["nodes"]
        # scenario_id = request_data["scenario_id"]
        # uncomment above line and reomve below if need to pass scenario_id
        scenario_id = ""

        starttime = time.time()
        logger.info("Reporting: data preparation for marginal return curves is started")
        if len(nodes) == 0:
            nodesdf = pd.DataFrame.from_records(self.reporting_dao.touchpoints())
            nodes = nodesdf[nodesdf["level"] == "Variable"]["node_id"].values
            # nodes = [2002, 2003, 2004, 2005, 2006]
        df = pd.DataFrame.from_records(
            self.reporting_dao.get_marginal_return_curves_data(nodes, scenario_id)
        )
        # Addition for including Total Assets
        df_total = df[df["outcome"] != "O_NTFHH_CNT"]
        df_total = (
            df_total.groupby(["node_id", "spend_change", "node_display_name"])[
                ["value", "value_change"]
            ]
            .sum()
            .reset_index()
        )
        df_total["outcome"] = "O_ASSET_IN"
        df = pd.concat([df, df_total])
        base_spend_list = self.reporting_dao.get_marginal_return_curves_base_spend_data(
            nodes, scenario_id
        )
        base_spend_data = dict(
            [(x["node_display_name"], x["base_spend"]) for x in base_spend_list]
        )
        node_name_list = df["node_display_name"].unique()
        results = {
            "outcome1": [],
            "outcome2": [],
        }
        delta = {
            "outcome1": {},
            "outcome2": {},
        }

        for node in node_name_list:
            node_df_ntf_asset = df[
                (df["node_display_name"] == node) & (df["outcome"] == "outcome1")
            ]
            node_df_exi_asset = df[
                (df["node_display_name"] == node) & (df["outcome"] == "outcome2")
            ]
            # node_df_total_asset = df[
            #     (df["node_display_name"] == node) & (df["outcome"] == "O_ASSET_IN")
            # ]
            # node_df_ntf_count = df[
            #     (df["node_display_name"] == node) & (df["outcome"] == "O_NTFHH_CNT")
            # ]

            # filter out duplicate values with same node name
            node_id_list = node_df_exi_asset["node_id"].unique().tolist()
            if len(node_id_list) > 1:
                min_node_id = min(node_id_list)
                node_df_ntf_asset = node_df_ntf_asset[
                    node_df_ntf_asset["node_id"] == min_node_id
                ]
                node_df_exi_asset = node_df_exi_asset[
                    node_df_exi_asset["node_id"] == min_node_id
                ]
                # node_df_total_asset = node_df_total_asset[
                #     node_df_total_asset["node_id"] == min_node_id
                # ]
                # node_df_ntf_count = node_df_ntf_count[
                #     node_df_ntf_count["node_id"] == min_node_id
                # ]
            results["outcome1"].append(
                ["spend_change:" + node] + node_df_ntf_asset["spend_change"].tolist()
            )
            results["outcome2"].append(
                ["spend_change:" + node] + node_df_exi_asset["spend_change"].tolist()
            )
            # results["Total_Assets_In"].append(
            #     ["spend_change:" + node] + node_df_total_asset["spend_change"].tolist()
            # )
            # results["NTF_HH_Count"].append(
            #     ["spend_change:" + node] + node_df_ntf_count["spend_change"].tolist()
            # )

            delta["outcome1"][node] = node_df_ntf_asset["value_change"].tolist()
            delta["outcome2"][node] = node_df_exi_asset["value_change"].tolist()
            # delta["Total_Assets_In"][node] = node_df_total_asset[
            #     "value_change"
            # ].tolist()
            # delta["NTF_HH_Count"][node] = node_df_ntf_count["value_change"].tolist()

            results["outcome1"].append([node] + node_df_ntf_asset["value"].tolist())
            results["outcome2"].append([node] + node_df_exi_asset["value"].tolist())
            # results["Total_Assets_In"].append(
            #     [node] + node_df_total_asset["value"].tolist()
            # )
            # results["NTF_HH_Count"].append([node] + node_df_ntf_count["value"].tolist())

        endtime = time.time()
        print(endtime - starttime)
        logger.info(
            "Reporting: data preparation for marginal return curves is completed in %s",
            (endtime - starttime),
        )
        if len(nodes1) == 0:
            base_spend_data1 = dict()
            result1 = dict()
            result1["outcome1"] = []
            result1["outcome2"] = []
            delta1 = dict()
            delta1["outcome1"] = dict()
            delta1["outcome2"] = dict()
            base_spend_data = dict(
                sorted(base_spend_data.items(), key=lambda item: item[1], reverse=True)
            )
            for i in list(base_spend_data.keys())[:3]:
                base_spend_data1[i] = base_spend_data[i]
                for j in results["outcome1"]:
                    if i in j[0]:
                        result1["outcome1"].append(j)
                for j in results["outcome2"]:
                    if i in j[0]:
                        result1["outcome2"].append(j)
                delta1["outcome1"][i] = delta["outcome1"][i]
                delta1["outcome2"][i] = delta["outcome2"][i]
            return {
                "results": result1,
                "delta": delta1,
                "base_spend_data": base_spend_data1,
            }
        else:
            return {
                "results": results,
                "delta": delta,
                "base_spend_data": base_spend_data,
            }

    def fetch_spend_allocation_data(self, request_data):
        starttime = time.time()
        scenario_1 = int(request_data["scenario_1"]) or 1
        scenario_2 = int(request_data["scenario_2"]) or 2
        period_type = request_data["period_type"] or "year"
        outcome = request_data["outcome"] or "outcome2"
        is_required_control = request_data["required_control"]
        year1 = int(request_data["year1"])
        year2 = int(request_data["year2"])
        if period_type == "quarter":
            quarter1 = request_data["quarter1"]
            quarter2 = request_data["quarter2"]
        if period_type == "month":
            month1 = request_data["month1"]
            month2 = request_data["month2"]

        if outcome == "outcome2":
            outcome = "outcome2"
        elif outcome == "outcome1":
            outcome = "outcome1"
        if is_required_control:
            node_id = 2000
        else:
            node_id = 4000

        s1_results = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations(
                year1, year2, outcome, period_type
            )
        )
        s1_results["allocation"] = s1_results["allocation"].astype(float)
        s2_results = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations(
                year2, year1, outcome, period_type
            )
        )
        s2_results["allocation"] = s2_results["allocation"].astype(float)
        s1_spends = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_details(year1, year2, period_type)
        )
        s1_spends["spend_value"] = s1_spends["spend_value"].astype(float)
        s2_spends = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_details(year2, year1, period_type)
        )
        s2_spends["spend_value"] = s2_spends["spend_value"].astype(float)

        # media_hierarchy = pd.DataFrame.from_records(self.reporting_dao.get_media_hierarchy_new()).sort_values(
        #     by=['node_seq', 'node_id'])

        ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
        # In case, we need DMA level reporting, comment this line and
        # uncomment the above lines
        media_hierarchy = pd.DataFrame.from_records(
            self.reporting_dao.touchpoints()
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
        # spend_allocation1 = media_hierarchy.merge(s1_results, on=['node_name', 'geo'], how='left').replace(r'^\s*$',
        #                                                                                                    np.nan,
        #                                                                                                    regex=True)

        ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
        # In case, we need DMA level reporting, comment this line and
        # uncomment the above line
        spend_allocation1 = media_hierarchy.merge(
            s1_results, on=["node_name"], how="left"
        ).replace(FORMAL_STRING, np.nan, regex=True)
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

        # spend_allocation2 = media_hierarchy.merge(s2_results, on=['node_name', 'geo'], how='left').replace(r'^\s*$',
        #                                                                                                    np.nan,
        #                                                                                                    regex=True)

        ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
        # In case, we need DMA level reporting, comment this line and
        # uncomment the above line
        spend_allocation2 = media_hierarchy.merge(
            s2_results, on=["node_name"], how="left"
        ).replace(FORMAL_STRING, np.nan, regex=True)
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
            self.reporting_dao.get_period_master_data(period_type)
        )
        periods = period_master["period_name"].unique()
        headers = self.get_tree_table_headers([year1, year2], periods)
        final = {"spends": [], "outcomes": [], "headers": headers, "cpa": []}

        for i, node in media_hierarchy[media_hierarchy["node_id"] > node_id].iterrows():
            ## Check for geo level spends
            # If there are no geo's(parent id), it'll sum up all the allocations and spend
            # If there is geo for a specific touchpoint, it'll filter for particular spend,
            # and allocation for that touchpoint and geo

            data1 = spend_allocation1[
                spend_allocation1["node_name"].isin(node.leaf_nodes)
            ]
            data2 = spend_allocation2[
                spend_allocation2["node_name"].isin(node.leaf_nodes)
            ]
            spend1 = s1_spends[s1_spends["node_name"].isin(node.leaf_nodes)]
            spend2 = s2_spends[s2_spends["node_name"].isin(node.leaf_nodes)]

            ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
            # In case, we need DMA level reporting, uncomment these lines
            # if node['geo'] is not None:
            #     data1 = data1[data1['geo'] == node['geo']]
            #     data2 = data2[data2['geo'] == node['geo']]
            #     spend1 = spend1[spend1['geo'] == node['geo']]
            #     spend2 = spend2[spend2['geo'] == node['geo']]

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
                        group_data_outcome11[i][1]=group_spend_s1[i][1]/group_data_s1[i][1]
                    # except:
                    #     group_data_outcome11[i][1] = group_spend_s1[i][1]
                    except:
                        group_data_outcome11[i][1] = group_spend_s1[i][1]
                        raise
            group_data_outcome12 = group_data_s2.copy()
            if group_data_s2 == [] or group_spend_s2 == []:
                group_data_outcome12 = []
            else:
                for i in range(len(group_spend_s2)):
                    try:
                        group_data_outcome12[i][1]=group_spend_s2[i][1]/group_data_s2[i][1]
                    # except:
                    #     group_data_outcome12[i][1] = group_spend_s2[i][1]
                    except:
                        group_data_outcome12[i][1] = group_spend_s2[i][1]
                        raise
            node_data_o1 = dict(group_data_outcome11)
            node_data_o2 = dict(group_data_outcome12)
            node_data_o1.update(node_data_o2)
            row_outcome1["node_data"] = node_data_o1
            final["cpa"].append(row_outcome1)
        spend_percent = []
        for i in final['spends']:
            if period_type == "year":
                if i['node_data']["Year_"+str(year1)] == 0 :
                    i['node_data']['percent']=0
                else:
                    i['node_data']['percent']=((i["node_data"]["Year_"+str(year2)]-i["node_data"]["Year_"+str(year1)])/i["node_data"]["Year_"+str(year1)])*100
                spend_percent.append(i)
            if period_type == "quarter":
                if i['node_data'][quarter1+"_"+str(year1)]== 0 :
                    i['node_data']['percent']=0
                else:
                    i['node_data']['percent']=((i["node_data"][quarter2+"_"+str(year2)]-i["node_data"][quarter1+"_"+str(year1)])/i["node_data"][quarter1+"_"+str(year1)])*100
                spend_percent.append(i)
            if period_type == "month":
                if i['node_data'][month1+"_"+str(year1)]== 0 :
                    i['node_data']['percent']=0
                else:
                    i['node_data']['percent']=((i["node_data"][month2+"_"+str(year2)]-i["node_data"][month1+"_"+str(year1)])/i["node_data"][month1+"_"+str(year1)])*100
                spend_percent.append(i)
        final["spends"]=spend_percent
        outcome_percent = []
        for i in final['outcomes']:
            if period_type == "year":
                if i['node_data']["Year_"+str(year1)] == 0 :
                    i['node_data']['percent']=0
                else:
                    i['node_data']['percent']=((i["node_data"]["Year_"+str(year2)]-i["node_data"]["Year_"+str(year1)])/i["node_data"]["Year_"+str(year1)])*100
                outcome_percent.append(i)
            if period_type == "quarter":
                if i['node_data'][quarter1+"_"+str(year1)]== 0 :
                    i['node_data']['percent']=0
                else:
                    i['node_data']['percent']=((i["node_data"][quarter2+"_"+str(year2)]-i["node_data"][quarter1+"_"+str(year1)])/i["node_data"][quarter1+"_"+str(year1)])*100
                outcome_percent.append(i)
            if period_type == "month":
                if i['node_data'][month1+"_"+str(year1)]== 0 :
                    i['node_data']['percent']=0
                else:
                    i['node_data']['percent']=((i["node_data"][month2+"_"+str(year2)]-i["node_data"][month1+"_"+str(year1)])/i["node_data"][month1+"_"+str(year1)])*100
                outcome_percent.append(i)
        final["outcomes"]=outcome_percent
        cpa_percent = []
        for i in final['cpa']:
            if period_type == "year":
                if i['node_data']["Year_"+str(year1)] == 0 :
                    i['node_data']['percent']=0
                else:
                    i['node_data']['percent']=((i["node_data"]["Year_"+str(year2)]-i["node_data"]["Year_"+str(year1)])/i["node_data"]["Year_"+str(year1)])*100
                cpa_percent.append(i)
            if period_type == "quarter":
                if i['node_data'][quarter1+"_"+str(year1)]== 0 :
                    i['node_data']['percent']=0
                else:
                    i['node_data']['percent']=((i["node_data"][quarter2+"_"+str(year2)]-i["node_data"][quarter1+"_"+str(year1)])/i["node_data"][quarter1+"_"+str(year1)])*100
                cpa_percent.append(i)
            if period_type == "month":
                if i['node_data'][month1+"_"+str(year1)]== 0 :
                    i['node_data']['percent']=0
                else:
                    i['node_data']['percent']=((i["node_data"][month2+"_"+str(year2)]-i["node_data"][month1+"_"+str(year1)])/i["node_data"][month1+"_"+str(year1)])*100
                cpa_percent.append(i)
        final["cpa"]=cpa_percent
        return final

    def fetch_soc_comparison_by_node(self, request_data):
        scenario_1 = int(request_data["scenario_1"]) or 1
        scenario_2 = int(request_data["scenario_2"]) or 2
        period_type = request_data["period_type"] or "year"
        outcome = request_data["outcome"] or "outcome2"
        nodes_data = request_data["nodes"] or [2003, 2005]
        nodes = [int(i) for i in nodes_data]
        year1 = int(request_data["year1"])
        year2 = int(request_data["year2"])

        if outcome == "outcome2":
            outcome = "outcome2"
        elif outcome == "outcome1":
            outcome = "outcome1"
        # nodes = request_data["nodes"] or [2003, 2005]
        customer_names = {
            "outcome2": "outcome2",
            "outcome1": "outcome1",
        }
        scenario_name_1_df = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_name(scenario_1)
        )
        scenario_name_1 = year1

        scenario_name_2_df = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_name(scenario_2)
        )
        scenario_name_2 = year2
        s1_results = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations(
                year1, year2, outcome, period_type
            )
        )
        s1_results["allocation"] = s1_results["allocation"].astype(float)
        s2_results = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations(
                year2, year1, outcome, period_type
            )
        )
        s2_results["allocation"] = s2_results["allocation"].astype(float)
        s1_spends = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_details(year1, year2, period_type)
        )
        s1_spends["spend_value"] = s1_spends["spend_value"].astype(float)
        s2_spends = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_details(year2, year1, period_type)
        )
        s2_spends["spend_value"] = s2_spends["spend_value"].astype(float)

        if request_data["period_type"] == "quarter":
            s1_results = s1_results[
                s1_results["quarter"] == request_data["quarter1"] + "_" + str(year1)
            ]
            s2_results = s2_results[
                s2_results["quarter"] == request_data["quarter2"] + "_" + str(year2)
            ]
            s1_spends = s1_spends[
                s1_spends["quarter"] == request_data["quarter1"] + "_" + str(year1)
            ]
            s2_spends = s2_spends[
                s2_spends["quarter"] == request_data["quarter2"] + "_" + str(year2)
            ]
        elif request_data["period_type"] == "month":
            s1_results = s1_results[
                s1_results["month"] == request_data["month1"] + "_" + str(year1)
            ]
            s2_results = s2_results[
                s2_results["month"] == request_data["month2"] + "_" + str(year2)
            ]
            s1_spends = s1_spends[
                s1_spends["month"] == request_data["month1"] + "_" + str(year1)
            ]
            s2_spends = s2_spends[
                s2_spends["month"] == request_data["month2"] + "_" + str(year2)
            ]
        # results = pd.merge(s1_results, s2_results, how="left", on=["node_name", "geo"])
        results = pd.merge(s1_results, s2_results, how="left", on=["node_name", "geo"], validate="many_to_many")
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
            self.reporting_dao.touchpoints()
        ).sort_values(by=["node_seq", "node_id"])

        media_hierarchy["leaf_nodes"] = media_hierarchy["leaf_nodes"].map(eval)

        # self.df = media_hierarchy.merge(results, on=['node_name', 'geo'], how='left').replace(r'^\s*$', np.nan,
        #                                                                                       regex=True)

        ## Fix for not reporting DMA level numbers --- Himanshu -- 05/07/2020
        # In case, we need DMA level reporting, comment this line and
        # comment the above line
        self.df = media_hierarchy.merge(results, on=["node_name"], how="left").replace(
            FORMAL_STRING, np.nan, regex=True
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
            relevant_nodes = media_hierarchy[(media_hierarchy["level"] == LEVEL_2) & (media_hierarchy["node_id"] < 2040)]["node_id"]
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
            row_spend[SPEND + str(scenario_name_1)] = s1_spends[
                s1_spends["node_name"].isin(node.leaf_nodes)
            ]["spend_value"].sum()
            row_spend[SPEND + str(scenario_name_2)] = s2_spends[
                s2_spends["node_name"].isin(node.leaf_nodes)
            ]["spend_value"].sum()
            if period_type == "year":
                row_spend[customer_names[outcome] + " " + str(scenario_name_1)] = data[
                    "scenario1"
                ].sum()
                row_spend[customer_names[outcome] + " " + str(scenario_name_2)] = data[
                    "scenario2"
                ].sum()
            elif period_type == "quarter":
                row_spend[customer_names[outcome] + " " +request_data["quarter1"] +" "+str(scenario_name_1)] = data[
                    "scenario1"
                ].sum()
                row_spend[customer_names[outcome] + " " +request_data["quarter2"]+" "+str(scenario_name_2)] = data[
                    "scenario2"
                ].sum()
            else:
                row_spend[customer_names[outcome] + " " +request_data["month1"] +" "+ str(scenario_name_1)] = data[
                    "scenario1"
                ].sum()
                row_spend[customer_names[outcome] + " " +request_data["month2"] +" "+ str(scenario_name_2)] = data[
                    "scenario2"
                ].sum()
            final.append(row_spend)
        sorted_data = sorted(final, key=lambda x: list(x.values())[4])[::-1]
        return sorted_data

    def fetch_spend_allocation_summary(self, request_data):
        scenario_1 = int(request_data["scenario_1"]) or 1
        scenario_2 = int(request_data["scenario_2"]) or 2
        period_type = request_data["period_type"] or "year"
        year1 = request_data["year1"]
        year2 = request_data["year2"]
        quarter1 = ""
        quarter2 = ""
        if period_type == "quarter":
            quarter1 = request_data["quarter1"]
            quarter2 = request_data["quarter2"]
        if period_type == "halfyear":
            quarter1 = request_data["halfyear1"]
            quarter2 = request_data["halfyear2"]
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
            quarter1 = d[request_data["month1"]]
            quarter2 = d[request_data["month2"]]
        # outcome = request_data['outcome'] or 'O_EXASSET_IN'
        # include_control = request_data["include_control"] or False

        include_control = request_data["required_control"]
        result = {}

        scenario_1_name = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_name(scenario_1)
        )
        # result["s1_name"] = scenario_1_name.iloc[0][0]
        result["s1_name"] = year1
        scenario_2_name = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_name(scenario_2)
        )
        result["s2_name"] = year2
        if period_type == "month":
            result["s1_name"] = result["s1_name"] + " " + request_data["month1"]
            result["s2_name"] = result["s2_name"] + " " + request_data["month2"]
        else:
            result["s1_name"] = result["s1_name"] + " " + quarter1
            result["s2_name"] = result["s2_name"] + " " + quarter2

        # Summary of spend
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_total_scenario_spend_details(
                int(year1), int(year2), period_type, quarter1
            )
        )
        result["s1_spends"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_total_scenario_spend_details(
                int(year2), int(year1), period_type, quarter2
            )
        )
        result["s2_spends"] = int(query_output.iloc[0][0])

        # Summary of outcomes
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_total(
                int(year1),
                int(year2),
                "outcome2",
                include_control,
                period_type,
                quarter1,
            )
        )
        result["s1_outcome2"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_total(
                int(year1),
                int(year2),
                "outcome1",
                include_control,
                period_type,
                quarter1,
            )
        )
        result["s1_outcome1"] = int(query_output.iloc[0][0])
    
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_total(
                int(year2),
                int(year1),
                "outcome2",
                include_control,
                period_type,
                quarter2,
            )
        )
        result["s2_outcome2"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_total(
                int(year2),
                int(year1),
                "outcome1",
                include_control,
                period_type,
                quarter2,
            )
        )
        result["s2_outcome1"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_total_cftbs(
                int(year2),
                int(year1),
                "outcome1",
                include_control,
                period_type,
                quarter2,
            )
        )
        result["s2_coutcome1"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_total_cftbs(
                int(year1),
                int(year2),
                "outcome1",
                include_control,
                period_type,
                quarter2,
            )
        )
        result["s1_coutcome1"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_total_cftbs(
                int(year1),
                int(year2),
                "outcome2",
                include_control,
                period_type,
                quarter2,
            )
        )
        result["s1_coutcome2"] = int(query_output.iloc[0][0])
        query_output = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_total_cftbs(
                int(year2),
                int(year1),
                "outcome2",
                include_control,
                period_type,
                quarter2,
            )
        )
        result["s2_coutcome2"] = int(query_output.iloc[0][0])
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
        return result

    def download_reporting_allocations(self, request_data):
        allocation_year = int(request_data.get("year"))
        period_type = "year"
        quarter = request_data.get("quarter")
        month = int(request_data.get("month"))

        allocation_df = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_allocations_download(
                allocation_year, period_type, quarter, month
            )
        )
        allocation_df["value"] = allocation_df["value"].astype(float)
        if period_type == "year" or period_type == "month":
            query_result_wide = pd.pivot_table(
                allocation_df,
                values="value",
                index=["node_name", "quarter", "geo", "month"],
                columns="outcome",
            )
        else:
            query_result_wide = pd.pivot_table(
                allocation_df,
                values="value",
                index=["node_name", "geo"],
                columns="outcome",
            )

        spend = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_download(
                allocation_year, period_type, quarter, month
            )
        )
        spend["spend_value"] = spend["spend_value"].astype(float)
        if period_type == "year" or period_type == "month":
            # data = query_result_wide.merge(
            #     spend, on=["node_name", "quarter", "geo", "month"], how="left"
            # ).fillna(0)
            data = query_result_wide.merge(
                spend, on=["node_name", "quarter", "geo", "month"], how="left", validate=None
            ).fillna(0)
        else:
            # data = query_result_wide.merge(
            #     spend, on=["node_name", "geo"], how="left"
            # ).fillna(0)
            data = query_result_wide.merge(
                spend, on=["node_name", "geo"], how="left", validate=None
            ).fillna(0)

        # media_hierarchy = pd.DataFrame.from_records(self.reporting_dao.get_media_hierarchy_new()).sort_values(
        #     by=['node_seq', 'node_id'])

        ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
        # In case, we need DMA level reporting, comment this line and
        # uncomment the above line
        media_hierarchy = pd.DataFrame.from_records(
            self.reporting_dao.touchpoints()
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
        final = []
        control_base_leaf_nodes = media_hierarchy[media_hierarchy["node_id"] == 6000][
            "leaf_nodes"
        ].iloc[0]
        base_leaf_nodes = media_hierarchy[media_hierarchy["node_id"] == 4000][
            "leaf_nodes"
        ].iloc[0]
        media_leaf_nodes = media_hierarchy[media_hierarchy["node_id"] == 2001][
            "leaf_nodes"
        ].iloc[0]
        control_base_data = data[data["node_name"].isin(eval(control_base_leaf_nodes))]
        media_data = data[data["node_name"].isin(eval(media_leaf_nodes))]
        base_data = data[data["node_name"].isin(eval(base_leaf_nodes))]
        base_data["O_TOTALASSET_IN"]=(base_data["outcome1"]+base_data["outcome2"])
        control_base_data["O_TOTALASSET_IN"] = (
            control_base_data["outcome1"] + control_base_data["outcome2"]
        )
        media_data["O_TOTALASSET_IN"] = media_data["outcome1"] + media_data["outcome2"]
        """
        Function to calculate all metrics for 1 row 
        (added by Manish on 09/30/2021)
        (modified by Mayank and Sidharth on 04/26/2022)
        """

        def calc_metrics(
            node,
            allocation_year,
            quarter,
            month,
            filtered_df,
            control_base_data,
            media_data,
            base_data,
            period=period_type,
        ):
            row = {}
            row["node_id"] = node["node_id"]
            row["Year"] = allocation_year
            row["Quarter"] = "Q" + str(quarter)
            row["Month"] = month
            # row['segment'] = seg

            """
            the following lines will take into consideration the period type and will perform attribution calculation
            when calculating yearly - the attributions were calculated at yearly level when report was being 
            downloaded at yearly level however we need the attributions to be at quarterly, i.e. at quarterly level the 
            attribution should add up to 100%
            """

            if period == "year" or period_type == "month":
                total_spend = round(filtered_df["spend_value"].sum(), 5)
                row["Spend"] = total_spend
                # Assuming node_id is a variable or column containing the node ID value

                node_id = node["node_id"]

                if node_id > 6000:
                    denominator = control_base_data[control_base_data["month"] == month]["spend_value"].sum()
                elif node_id > 4000:
                    denominator = base_data[base_data["month"] == month]["spend_value"].sum()
                else:
                    denominator = media_data[media_data["month"] == month]["spend_value"].sum()

                row["Spend_Attribution"] = round(filtered_df["spend_value"].sum() / denominator * 100, 5)

                # row["Spend_Attribution"] = (
                #     round(
                #         filtered_df["spend_value"].sum()
                #         / control_base_data[control_base_data["quarter"] == quarter][
                #             "spend_value"
                #         ].sum()
                #         * 100,
                #         5,
                #     )
                #     if node["node_id"] > 4000
                #     else round(
                #         filtered_df["spend_value"].sum()
                #         / media_data[media_data["quarter"] == quarter][
                #             "spend_value"
                #         ].sum()
                #         * 100,
                #         5,
                #     )
                # )

                for outcome in ("outcome2", "outcome1", "O_TOTALASSET_IN"):
                    row[outcome] = round(filtered_df[outcome].sum(), 5)
                    sumvalue = control_base_data[control_base_data["month"] == month][outcome].sum()+base_data[base_data["month"] == month][outcome].sum()+media_data[media_data["month"] == month][outcome].sum()
                    row[f"{outcome}_Attribution"] = (
                        round(
                            filtered_df[outcome].sum()
                            / sumvalue
                            * 100,
                            5,
                        )
                        if node["node_id"] > 4000
                        else round(
                            filtered_df[outcome].sum()
                            / sumvalue
                            * 100,
                            5,
                        )
                    )
                    row[f"{outcome}_efficiency"] = (
                        round(
                            row[f"{outcome}_Attribution"]
                            / row["Spend_Attribution"]
                            * 100,
                            2,
                        )
                        / 100
                    )
                    if outcome == "outcome1":
                        coutcome = outcome +"_c_outcome1($)"
                    if outcome == "outcome2":
                        coutcome = outcome + "_c_outcome2($)"
                    row[f"{coutcome}"] = round(row["Spend"] /row[outcome], 0)
                row["outcome2_CNT"] = round(filtered_df["outcome2"].sum(), 5)
                row["outcome2_CNT_Attribution"] = (
                    round(
                        filtered_df["outcome2"].sum()
                        / control_base_data[control_base_data["quarter"] == quarter][
                            "outcome2"
                        ].sum()
                        * 100,
                        5,
                    )
                    if node["node_id"] > 4000
                    else round(
                        filtered_df["outcome2"].sum()
                        / media_data[media_data["quarter"] == quarter][
                            "outcome2"
                        ].sum()
                        * 100,
                        5,
                    )
                )
                row["outcome2_CNT_efficiency"] = (
                    round(
                        row["outcome2_CNT_Attribution"] / row["Spend_Attribution"] * 100,
                        5,
                    )
                    / 100
                )
                row["outcome2_CNT_CPA"] = round(row["Spend"] / row["outcome2_CNT"], 5)

            # previous method - now used only during quarter calculation
            else:
                total_spend = round(filtered_df["spend_value"].sum(), 5)
                row["Spend"] = total_spend
                row["Spend_Attribution"] = (
                    round(
                        filtered_df["spend_value"].sum()
                        / control_base_data["spend_value"].sum()
                        * 100,
                        5,
                    )
                    if node["node_id"] > 4000
                    else round(
                        filtered_df["spend_value"].sum()
                        / media_data["spend_value"].sum()
                        * 100,
                        5,
                    )
                )

                for outcome in ("outcome2", "outcome1", "O_TOTALASSET_IN"):
                    row[outcome] = round(filtered_df[outcome].sum(), 5)
                    row[f"{outcome}_Attribution"] = (
                        round(
                            filtered_df[outcome].sum()
                            / control_base_data[outcome].sum()
                            * 100,
                            5,
                        )
                        if node["node_id"] > 4000
                        else round(
                            filtered_df[outcome].sum()
                            / media_data[outcome].sum()
                            * 100,
                            5,
                        )
                    )
                    row[f"{outcome}_efficiency"] = (
                        round(
                            row[f"{outcome}_Attribution"]
                            / row["Spend_Attribution"]
                            * 100,
                            5,
                        )
                        / 100
                    )
                    if outcome == "outcome1":
                        coutcome = outcome +"_c_outcome1($)"
                    if outcome == "outcome2":
                        coutcome = outcome + "_c_outcome2($)"
                    row[f"{coutcome}"] = round(row[outcome] / row["Spend"], 5)

                row["outcome2_CNT"] = round(filtered_df["outcome2"].sum(), 5)
                row["outcome2_CNT_Attribution"] = (
                    round(
                        filtered_df["outcome2"].sum()
                        / control_base_data["outcome2"].sum()
                        * 100,
                        5,
                    )
                    if node["node_id"] < 2000
                    else round(
                        filtered_df["outcome2"].sum()
                        / media_data["outcome2"].sum()
                        * 100,
                        5,
                    )
                )
                row["outcome2_CNT_efficiency"] = (
                    round(
                        row["outcome2_CNT_Attribution"] / row["Spend_Attribution"] * 100,
                        5,
                    )
                    / 100
                )
                row["outcome2_CNT_CPA"] = round(row["Spend"] / row["outcome2_CNT"], 5)
            return row

        if period_type == "year" or period_type == "month":
            for i, node in media_hierarchy.iterrows():
                # for seg in data['segment'].unique():
                for quarter in data["quarter"].unique():
                    for mo in data[data["quarter"] == quarter]["month"].unique():
                        # ## Check for geo level spends
                        # # If there are no geo's(parent id), it'll sum up all the allocations and spend
                        # # If there is geo for a specific touchpoint, it'll filter for particular spend,
                        # # and allocation for that touchpoint and geo
                        # if node['geo'] is None:
                        #     filtered_df = data[data['node_name'].isin(eval(node.leaf_nodes))]
                        # else:
                        #     if(DMA_FLAG == 1):
                        #         filtered_df = data[data['node_name'].isin(eval(node.leaf_nodes))]
                        #         filtered_df = filtered_df[filtered_df['geo'] == node['geo']]
                        #     else:
                        #         continue

                        ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
                        # In case, we need DMA level reporting, comment this line and
                        # uncomment the above lines
                        filtered_df = data[
                            data["node_name"].isin(eval(node.leaf_nodes))
                        ]
                        # filtered_df = filtered_df[filtered_df['segment'] == seg]
                        filtered_df = filtered_df[
                            (filtered_df["quarter"] == quarter)
                            & (filtered_df["month"] == mo)
                        ]
                        filtered_df["O_TOTALASSET_IN"] = (
                            filtered_df["outcome1"] + filtered_df["outcome2"]
                        )
                        final.append(
                            calc_metrics(
                                node,
                                allocation_year,
                                quarter,
                                mo,
                                filtered_df,
                                control_base_data,
                                media_data,
                                base_data,
                                period_type,
                            )
                        )

        else:
            for i, node in media_hierarchy.iterrows():
                # for seg in data['segment'].unique():
                for mo in data["month"].unique():
                    ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
                    # In case, we need DMA level reporting, comment this line and
                    # uncomment the above lines
                    filtered_df = data[data["node_name"].isin(eval(node.leaf_nodes))]
                    # filtered_df = filtered_df[filtered_df['segment'] == seg]
                    filtered_df = filtered_df[filtered_df["month"] == mo]

                    filtered_df["O_TOTALASSET_IN"] = (
                        filtered_df["outcome1"] + filtered_df["outcome2"]
                    )

                    final.append(
                        calc_metrics(
                            node,
                            allocation_year,
                            quarter,
                            mo,
                            filtered_df,
                            control_base_data,
                            media_data,
                            period_type,
                        )
                    )
        final_df = pd.DataFrame(final).replace([np.inf, -np.inf], np.nan).fillna(0)

        final_df["Spend"] = final_df["Spend"].map(CURRENCY_FORMAT.format)
        final_df["outcome1"] = final_df["outcome1"].map("${:,.1f}".format)
        final_df["outcome2"] = final_df["outcome2"].map("{:,.1f}".format)
        # final_df["O_NTFASSET_IN"] = final_df["O_NTFASSET_IN"].map("${:,.1f}".format)
        final_df["O_TOTALASSET_IN"] = final_df["O_TOTALASSET_IN"].map("${:,.1f}".format)
        final_df["outcome1_Attribution"] = final_df["outcome1_Attribution"].map(
            PERCENTAGE_FORMAT.format
        )
        final_df["outcome1_efficiency"] = final_df["outcome1_efficiency"].map(
            DECIMAL_FORMAT.format
        )
        # final_df["O_NTFHH_CNT_Attribution"] = final_df["O_NTFHH_CNT_Attribution"].map(
        #     PERCENTAGE_FORMAT.format
        # )
        # final_df["O_NTFHH_CNT_efficiency"] = final_df["O_NTFHH_CNT_efficiency"].map(
        #     DECIMAL_FORMAT.format
        # )
        final_df["outcome2_Attribution"] = final_df["outcome2_Attribution"].map(
            PERCENTAGE_FORMAT.format
        )
        final_df["outcome2_efficiency"] = final_df["outcome2_efficiency"].map(
            DECIMAL_FORMAT.format
        )
        final_df["O_TOTALASSET_IN_Attribution"] = final_df[
            "O_TOTALASSET_IN_Attribution"
        ].map(PERCENTAGE_FORMAT.format)
        final_df["O_TOTALASSET_IN_efficiency"] = final_df[
            "O_TOTALASSET_IN_efficiency"
        ].map(DECIMAL_FORMAT.format)
        final_df["Spend_Attribution"] = final_df["Spend_Attribution"].map(
            PERCENTAGE_FORMAT.format
        )

        # full_media_hierarchy = pd.DataFrame.from_records(
        #     self.reporting_dao.get_media_hierarchy_download_data()).sort_values(by=['node_seq', 'node_id'])

        ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
        # In case, we need DMA level reporting, comment this line and
        # uncomment the above line
        full_media_hierarchy = pd.DataFrame.from_records(
            self.reporting_dao.get_media_hierarchy_old_download_data()
        ).sort_values(by=["node_seq", "node_id"])
        result = pd.merge(full_media_hierarchy, final_df, how="right", on=["node_id"], validate="many_to_many")
        result.insert(2, 'External Factors/Marketing/Base', result['node_id'].apply(lambda x: 'External Factors' if x >= 6000 else ('Base' if x >= 4000 else 'Marketing')))

        result.drop(["node_seq", "node_id"], axis=1, inplace=True)
        result.drop(
            [
                "outcome2_CNT",
                "outcome2_CNT_Attribution",
                "outcome2_CNT_efficiency",
                "outcome2_CNT_CPA",
                "O_TOTALASSET_IN_efficiency",
                "O_TOTALASSET_IN_Attribution",
                "O_TOTALASSET_IN",
            ],
            axis=1,
            inplace=True,
        )
        # if period_type == "month":
        #     result = result[
        #         (result["Year"] == allocation_year) & (result["Month"] == int(month))
        #     ]
        result["level"]=result["level"].apply(lambda x:LEVEL_3 if x=="Variable" else x)
        return result

    def download_soc_data(self, request_data):
        if request_data:
            scenarios = eval(request_data["scenarios"]) or [1, 2]
            period_type = str(request_data["period_type"])
            if period_type == "halfyear":
                periods = eval(request_data["halfyears"])
            elif period_type == "month":
                periods = eval(request_data["months"])
            else:
                periods = eval(request_data["quarters"])
            if str(request_data["outcome"]) == "Overall-Change":
                customer_list = ["outcome1", "outcome2"]
            elif str(request_data["outcome"]) == "TOTAL_ASSET_IN":
                customer_list = ["outcome1", "outcome2"]
            else:
                outcome = request_data["outcome"]
                if outcome == "outcome1":
                    outcome = "outcome1"
                else:
                    outcome = "outcome2"
                customer_list = [str(outcome)]
        else:
            scenarios = [1, 2]
            period_type = "year"
            customer_list = ["outcome2", "outcome1"]

        # Get scenario id from scenario_list
        scenario_1 = scenarios[0]
        scenario_2 = scenarios[1]

        # Get scenario name
        years = eval(request_data["years"])
        year_1 = years[0]
        year_2 = years[1]

        # Period Name
        period_1, period_2 = "", ""

        # Get media hierarchy

        # media_hierarchy = pd.DataFrame.from_records(self.reporting_dao.get_media_hierarchy_new()).sort_values(
        #     by=['node_seq', 'node_id'])

        ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
        # In case, we need DMA level reporting, comment this line and
        # uncomment the above line
        media_hierarchy = pd.DataFrame.from_records(
            self.reporting_dao.touchpoints()
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
        final = []  # Output dataframe
        if len(customer_list) == 1:
            customer = customer_list[0]

            ## Get allocations for each customer for individual scenarios for a specific period
            allocation_df_1 = pd.DataFrame.from_records(
                self.reporting_dao.get_scenario_spend_allocations_download(
                    int(year_1), int(year_2), period_type
                )
            )
            allocation_df_1.rename(
                columns={
                    "allocation": "allocation" + "_" + str(scenario_1),
                    "period_name": "period_name" + "_" + str(scenario_1),
                },
                inplace=True,
            )
            allocation_df_2 = pd.DataFrame.from_records(
                self.reporting_dao.get_scenario_spend_allocations_download(
                    int(year_2), int(year_1), period_type
                )
            )
            allocation_df_2.rename(
                columns={
                    "allocation": "allocation" + "_" + str(scenario_2),
                    "period_name": "period_name" + "_" + str(scenario_2),
                },
                inplace=True,
            )

            ## Calculate spends for each scenario and period type
            spend_df_1 = pd.DataFrame.from_records(
                self.reporting_dao.get_scenario_spend_details_download(
                    int(year_1), int(year_2), period_type
                )
            )
            spend_df_1.rename(
                columns={
                    "spend_value": "spend_value" + "_" + str(scenario_1),
                    "period_name": "period_name" + "_" + str(scenario_1),
                },
                inplace=True,
            )
            spend_df_2 = pd.DataFrame.from_records(
                self.reporting_dao.get_scenario_spend_details_download(
                    int(year_2), int(year_1), period_type
                )
            )
            spend_df_2.rename(
                columns={
                    "spend_value": "spend_value" + "_" + str(scenario_2),
                    "period_name": "period_name" + "_" + str(scenario_2),
                },
                inplace=True,
            )
            if period_type != "year":
                period_1 = periods[0]  # First period_name(e.g Q1, H2 etc.)
                period_2 = periods[1]  # Second period_name(e.g Q1, H2 etc.)

                ## Filter the spends and allocation dataframes for specific period
                spend_df_1 = spend_df_1[
                    spend_df_1["period_name" + "_" + str(scenario_1)]
                    == (period_1 + "_" + str(year_1))
                ]
                allocation_df_1 = allocation_df_1[
                    allocation_df_1["period_name" + "_" + str(scenario_1)]
                    == (period_1 + "_" + str(year_1))
                ]
                spend_df_2 = spend_df_2[
                    spend_df_2["period_name" + "_" + str(scenario_2)]
                    == (period_2 + "_" + str(year_2))
                ]
                allocation_df_2 = allocation_df_2[
                    allocation_df_2["period_name" + "_" + str(scenario_2)]
                    == (period_2 + "_" + str(year_2))
                ]

            # Get single dataframe for allocation and spends by merging individual dataframes
            allocation_df = allocation_df_1.merge(
                allocation_df_2, on=["outcome", "node_name", "geo"], how="inner"
            )
            spend_df = spend_df_1.merge(
                spend_df_2, on=["node_name", "geo"], how="inner"
            )

            for i, node in media_hierarchy.iterrows():
                # if node['geo'] is None:
                #     allocation_node_df = allocation_df[allocation_df['node_name'].isin(eval(node.leaf_nodes))]
                #     spend_node_df = spend_df[spend_df['node_name'].isin(eval(node.leaf_nodes))]
                # else:
                #     allocation_node_df = allocation_node_df[allocation_node_df['node_name'].isin(eval(node.leaf_nodes))]
                #     allocation_node_df = allocation_node_df[allocation_node_df['geo'] == node['geo']]
                #     spend_node_df = spend_df[spend_df['node_name'].isin(eval(node.leaf_nodes))]
                #     spend_node_df = spend_node_df[spend_node_df['geo'] == node['geo']]

                ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
                # In case, we need DMA level reporting, comment this line and
                # uncomment the above line
                allocation_node_df = allocation_df[
                    allocation_df["node_name"].isin(eval(node.leaf_nodes))
                ]
                spend_node_df = spend_df[
                    spend_df["node_name"].isin(eval(node.leaf_nodes))
                ]

                row = {}
                row["node_id"] = node["node_id"]
                customer_df = allocation_node_df[
                    allocation_node_df["outcome"] == customer
                ]  # For specific customer type

                row[year_1 + " " + period_1 + ":" + SPENDS] = round(
                    spend_node_df["spend_value" + "_" + str(scenario_1)].sum()
                )
                row[year_1 + " " + period_1 + ": " + customer] = round(
                    customer_df["allocation" + "_" + str(scenario_1)].sum()
                )

                row[year_2 + " " + period_2 + ":" + SPENDS] = round(
                    spend_node_df["spend_value" + "_" + str(scenario_2)].sum()
                )
                row[year_2 + " " + period_2 + ": " + customer] = round(
                    customer_df["allocation" + "_" + str(scenario_2)].sum()
                )
                final.append(row)
            final_df = pd.DataFrame(final).replace([np.inf, -np.inf], np.nan).fillna(0)

        else:
            ## Calculate spends for each scenario and period type
            # As spends remain same for each customer, hence, quering for one time only
            spend_df_1 = pd.DataFrame.from_records(
                self.reporting_dao.get_scenario_spend_details_download(
                    int(year_1), int(year_2), period_type
                )
            )
            spend_df_1.rename(
                columns={
                    "spend_value": "spend_value" + "_" + str(scenario_1),
                    "period_name": "period_name" + "_" + str(scenario_1),
                },
                inplace=True,
            )
            spend_df_2 = pd.DataFrame.from_records(
                self.reporting_dao.get_scenario_spend_details_download(
                    int(year_2), int(year_1), period_type
                )
            )
            spend_df_2.rename(
                columns={
                    "spend_value": "spend_value" + "_" + str(scenario_2),
                    "period_name": "period_name" + "_" + str(scenario_2),
                },
                inplace=True,
            )

            ## Get allocations for each customer for individual scenarios for a specific period
            allocation_df_1 = pd.DataFrame.from_records(
                self.reporting_dao.get_scenario_spend_allocations_download(
                    int(year_1), int(year_2), period_type
                )
            )
            allocation_df_1.rename(
                columns={
                    "allocation": "allocation" + "_" + str(scenario_1),
                    "period_name": "period_name" + "_" + str(scenario_1),
                },
                inplace=True,
            )
            allocation_df_2 = pd.DataFrame.from_records(
                self.reporting_dao.get_scenario_spend_allocations_download(
                    int(year_2), int(year_1), period_type
                )
            )
            allocation_df_2.rename(
                columns={
                    "allocation": "allocation" + "_" + str(scenario_2),
                    "period_name": "period_name" + "_" + str(scenario_2),
                },
                inplace=True,
            )

            if period_type != "year":
                period_1 = periods[0]  # First period_name(e.g Q1, H2 etc.)
                period_2 = periods[1]  # Second period_name(e.g Q1, H2 etc.)

                ## Filter the spends and allocation dataframes for specific period
                spend_df_1 = spend_df_1[
                    spend_df_1["period_name" + "_" + str(scenario_1)]
                    == (period_1 + "_" + str(year_1))
                ]
                allocation_df_1 = allocation_df_1[
                    allocation_df_1["period_name" + "_" + str(scenario_1)]
                    == (period_1 + "_" + str(year_1))
                ]
                spend_df_2 = spend_df_2[
                    spend_df_2["period_name" + "_" + str(scenario_2)]
                    == (period_2 + "_" + str(year_2))
                ]
                allocation_df_2 = allocation_df_2[
                    allocation_df_2["period_name" + "_" + str(scenario_2)]
                    == (period_2 + "_" + str(year_2))
                ]

            # Get single dataframe for allocation and spends by merging individual dataframes
            allocation_df = allocation_df_1.merge(
                allocation_df_2, on=["outcome", "node_name", "geo"], how="inner"
            )
            spend_df = spend_df_1.merge(
                spend_df_2, on=["node_name", "geo"], how="inner"
            )
            for i, node in media_hierarchy.iterrows():
                # if node['geo'] is None:
                #     allocation_node_df = allocation_df[allocation_df['node_name'].isin(eval(node.leaf_nodes))]
                #     spend_node_df = spend_df[spend_df['node_name'].isin(eval(node.leaf_nodes))]
                # else:
                #     allocation_node_df = allocation_node_df[allocation_node_df['node_name'].isin(eval(node.leaf_nodes))]
                #     allocation_node_df = allocation_node_df[allocation_node_df['geo'] == node['geo']]
                #     spend_node_df = spend_df[spend_df['node_name'].isin(eval(node.leaf_nodes))]
                #     spend_node_df = spend_node_df[spend_node_df['geo'] == node['geo']]

                ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
                # In case, we need DMA level reporting, comment this line and
                # uncomment the above line
                allocation_node_df = allocation_df[
                    allocation_df["node_name"].isin(eval(node.leaf_nodes))
                ]
                spend_node_df = spend_df[
                    spend_df["node_name"].isin(eval(node.leaf_nodes))
                ]

                row = {}
                row["node_id"] = node["node_id"]

                row[year_1 + " " + period_1 + ":" + SPENDS] = round(
                    spend_node_df["spend_value" + "_" + str(scenario_1)].sum()
                )
                # Get allocations for all types of customer in customer list for first scenario
                if str(request_data["outcome"]) == "TOTAL_ASSET_IN":
                    customer_df = allocation_node_df[
                        allocation_node_df["outcome"].isin(customer_list)
                    ]
                    row[year_1 + " " + period_1 + ": TOTAL_ASSET_IN"] = round(
                        customer_df["allocation" + "_" + str(scenario_1)].sum()
                    )
                else:
                    for customer in customer_list:
                        customer_df = allocation_node_df[
                            allocation_node_df["outcome"] == customer
                        ]
                        row[year_1 + " " + period_1 + ": " + customer] = round(
                            customer_df["allocation" + "_" + str(scenario_1)].sum()
                        )

                row[year_2 + " " + period_2 + ":" + SPENDS] = round(
                    spend_node_df["spend_value" + "_" + str(scenario_2)].sum()
                )
                # Get allocations for all types of customer in customer list for second scenario
                if str(request_data["outcome"]) == "TOTAL_ASSET_IN":
                    customer_df = allocation_node_df[
                        allocation_node_df["outcome"].isin(customer_list)
                    ]
                    row[year_2 + " " + period_2 + ": TOTAL_ASSET_IN"] = round(
                        customer_df["allocation" + "_" + str(scenario_2)].sum()
                    )
                else:
                    for customer in customer_list:
                        customer_df = allocation_node_df[
                            allocation_node_df["outcome"] == customer
                        ]
                        row[year_2 + " " + period_2 + ": " + customer] = round(
                            customer_df["allocation" + "_" + str(scenario_2)].sum()
                        )

                final.append(row)

            final_df = pd.DataFrame(final).replace([np.inf, -np.inf], np.nan).fillna(0)

        ## Changing format of columns
        # For existing and ntf assets, column will contain dollar as a perfix
        # For ntfhh, it will just be a number
        # For spends, dollar will be added as prefix
        if str(request_data["outcome"]) != "Overall-Change":
            customer_value = "c" + customer_list[0]
            if customer_value == "coutcome2":
                customer_value = "coutcome2"
            final_df[final_df.columns[1].split(":")[0] + ": " + customer_value] = (
                final_df[final_df.columns[1]] / final_df[final_df.columns[2]]
            )
            final_df[final_df.columns[3].split(":")[0] + ": " + customer_value] = (
                final_df[final_df.columns[3]] / final_df[final_df.columns[4]]
            )
            final_df["spend(%)"]=round(((final_df[final_df.columns[1]]-final_df[final_df.columns[3]])/final_df[final_df.columns[3]])*100,2)
            final_df[customer_list[0]+"(%)"]=round(((final_df[final_df.columns[2]]-final_df[final_df.columns[4]])/final_df[final_df.columns[4]])*100,2)
            final_df[customer_value+"(%)"]=round(((final_df[final_df.columns[5]]-final_df[final_df.columns[6]])/final_df[final_df.columns[6]])*100,2)
        else:
            final_df[final_df.columns[1].split(":")[0] + ": coutcome1"] = (
                final_df[final_df.columns[1]] / final_df[final_df.columns[2]]
            )
            final_df[final_df.columns[1].split(":")[0] + ": coutcome2"] = (
                final_df[final_df.columns[1]] / final_df[final_df.columns[3]]
            )
            final_df[final_df.columns[4].split(":")[0] + ": coutcome1"] = (
                final_df[final_df.columns[4]] / final_df[final_df.columns[5]]
            )
            final_df[final_df.columns[4].split(":")[0] + ": coutcome2"] = (
                final_df[final_df.columns[4]] / final_df[final_df.columns[6]]
            )

        final_df = final_df.fillna(0)
        final_df = final_df.replace([np.inf, -np.inf], 0)
        for customer in customer_list:
            if customer == "outcome2" or customer == "outcome1":
                final_df[year_1 + " " + period_1 + ": " + customer] = final_df[
                    year_1 + " " + period_1 + ": " + customer
                ].map(FORMAT_STRING.format)
                final_df[year_2 + " " + period_2 + ": " + customer] = final_df[
                    year_2 + " " + period_2 + ": " + customer
                ].map(FORMAT_STRING.format)
            else:
                final_df[year_1 + " " + period_1 + ": " + customer] = final_df[
                    year_1 + " " + period_1 + ": " + customer
                ].map(FORMAT_STRING.format)
                final_df[year_2 + " " + period_2 + ": " + customer] = final_df[
                    year_2 + " " + period_2 + ": " + customer
                ].map(FORMAT_STRING.format)
        c_customers = []
        for i in customer_list:
            customer_value = "c" + i
            if customer_value == "coutcome2":
                customer_value = "coutcome2"
            c_customers.append(customer_value)
        for customer in c_customers:
            if customer == "coutcome2" or customer == "coutcome1":
                final_df[year_1 + " " + period_1 + ": " + customer] = final_df[
                    year_1 + " " + period_1 + ": " + customer
                ].map(CURRENCY_FORMAT.format)
                final_df[year_2 + " " + period_2 + ": " + customer] = final_df[
                    year_2 + " " + period_2 + ": " + customer
                ].map(CURRENCY_FORMAT.format)

        final_df[year_1 + " " + period_1 + ":" + SPENDS] = final_df[
            year_1 + " " + period_1 + ":" + SPENDS
        ].map(CURRENCY_FORMAT.format)
        final_df[year_2 + " " + period_2 + ":" + SPENDS] = final_df[
            year_2 + " " + period_2 + ":" + SPENDS
        ].map(CURRENCY_FORMAT.format)

        # full_media_hierarchy = pd.DataFrame.from_records(
        #     self.reporting_dao.get_media_hierarchy_download_data()).sort_values(by=['node_seq', 'node_id'])

        ## Fix for not reporting DMA level numbers --- Himanshu -- 01/07/2020
        # In case, we need DMA level reporting, comment this line and
        # uncomment the above line
        full_media_hierarchy = pd.DataFrame.from_records(
            self.reporting_dao.get_media_hierarchy_old_download_data()
        ).sort_values(by=["node_seq", "node_id"])
        result = pd.merge(full_media_hierarchy, final_df, how="right", on=["node_id"], validate="many_to_many")
        result.insert(2, 'External Factors/Marketing/Base', result['node_id'].apply(lambda x: 'External Factors' if x >= 6000 else ('Base' if x >= 4000 else 'Marketing')))
        result.drop(["node_seq", "node_id"], axis=1, inplace=True)
        result["level"]=result["level"].apply(lambda x:LEVEL_3 if x=="Variable" else x)

        return result

    # In[End]:
    def getSourceOfChange(self, data1, data2):
        scenario1 = data1.groupby("node_name")["allocation"].sum()
        scenario2 = data2.groupby("node_name")["allocation"].sum()
        soc_data = pd.concat({"scenario1": scenario1, "scenario2": scenario2}, axis=1)
        soc_data.fillna(0, inplace=True)
        soc_data["change"] = round(soc_data["scenario1"],0) - round(soc_data["scenario2"],0)
        soc_data["pct_change"] = soc_data["change"] / round(soc_data["scenario2"].sum(),0)
        soc = soc_data["pct_change"].rename("value").reset_index()
        return soc

    def fetch_soc_waterfall_chart_data(self, request_data):
        # year1 = scenario_1 = int(request_data["year1"]) or 1
        # year2 = scenario_2 = int(request_data["year2"]) or 2
        period_type = request_data["period_type"] or "year"
        quarter1 = ""
        quarter2 = ""
        month1 = ""
        month2 = ""
        halfyear1 = ""
        halfyear2 = ""
        if period_type == "quarter":
            quarter1 = request_data["quarter1"]
            quarter2 = request_data["quarter2"]
            # scenario_1 = self.reporting_dao.get_scenario_by_period(
            #     scenario_1, quarter1, "", period_type
            # )[0]["scenario_id"]
            # scenario_2 = self.reporting_dao.get_scenario_by_period(
            #     scenario_2, quarter2, "", period_type
            # )[0]["scenario_id"]
        elif period_type == "month":
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

            month1 = d[request_data["month1"]]
            month2 = d[request_data["month2"]]
            # scenario_1 = self.reporting_dao.get_scenario_by_period(
            #     scenario_1, "", month1, period_type
            # )[0]["scenario_id"]
            # scenario_2 = self.reporting_dao.get_scenario_by_period(
            #     scenario_2, "", month2, period_type
            # )[0]["scenario_id"]
        # elif period_type == "week":
        #     month1 = request_data["month1"]
        #     month2 = request_data["month2"]
        #     week1 = request_data["week1"]
        #     week2 = request_data["week2"]
        #     scenario_1 = self.reporting_dao.get_scenario_by_period(
        #         scenario_1, "", month1, period_type
        #     )[0]["scenario_id"]
        #     scenario_2 = self.reporting_dao.get_scenario_by_period(
        #         scenario_2, "", month2, period_type
        #     )[0]["scenario_id"]
        elif period_type == "halfyear":
            halfyear1 = request_data["halfyear1"]
            halfyear2 = request_data["halfyear2"]
        column_highlevel = "group1"
        column_controlsplit = "group4"
        column_mediasplit = "group3"
        column_econsplit = "group2"

        outcome = request_data["outcome"] or "outcome2"
        if outcome == "outcome2":
            outcome = "outcome2"
        elif outcome == "outcome1":
            outcome = "outcome1"
        reporting_groups = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_by_nodes()
        )
        # Fetch SOC data from SOC Table4 new_result['allocation'] = (new_result['allocation_x'] - new_result['allocation_y'])/new_result['allocation_x']
        s1_results = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_temp(
                scenario_1,
                scenario_2,
                outcome,
                period_type,
                quarter1,
                month1,
                halfyear1,
            )
        )
        s1_results["allocation"] = s1_results["allocation"].astype(float)
        s2_results = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_temp(
                scenario_2,
                scenario_1,
                outcome,
                period_type,
                quarter2,
                month2,
                halfyear2,
            )
        )
        s2_results["allocation"] = s2_results["allocation"].astype(float)
        soc_data = ReportingHandler().getSourceOfChange(s1_results, s2_results)
        if soc_data.empty:
            return "Data Not Found"
        soc_data = soc_data.merge(reporting_groups, how="inner", on="node_name")
        # pdb.set_trace()
        highLevelgroupeddata = soc_data.groupby(
            ["variable_type", column_highlevel]
        ).sum()
        highLevelgroupeddata.reset_index(inplace=True)
        highLevelgroupeddata["value"] = highLevelgroupeddata["value"].astype(float)
        highlevel_group_orders = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_orders(column_highlevel)
        )
        highLevelgroupeddata = highLevelgroupeddata.merge(
            highlevel_group_orders,
            how="inner",
            left_on=[column_highlevel],
            right_on=["group_name"],
        )
        highLevelgroupeddata.sort_values(by=["value"], ascending=[False], inplace=True)
        # pdb.set_trace()
        controlSplitgroupeddata = soc_data.groupby(
            [column_controlsplit, "group1"]
        ).sum()
        controlSplitgroupeddata.reset_index(inplace=True)
        controlSplitgroupeddata["value"] = controlSplitgroupeddata["value"].astype(
            float
        )
        control_group_order = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_orders(column_controlsplit)
        )
        controlSplitgroupeddata = controlSplitgroupeddata.merge(
            control_group_order,
            how="inner",
            left_on=[column_controlsplit],
            right_on=["group_name"],
        )
        controlSplitgroupeddata.sort_values(
            by=["order2", "value"], ascending=[True, False], inplace=True
        )

        mediaSplitgroupeddata = soc_data.groupby([column_mediasplit, "group1"]).sum()
        mediaSplitgroupeddata.reset_index(inplace=True)
        mediaSplitgroupeddata["value"] = mediaSplitgroupeddata["value"].astype(float)
        media_group_order = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_orders(column_mediasplit)
        )
        mediaSplitgroupeddata = mediaSplitgroupeddata.merge(
            media_group_order,
            how="inner",
            left_on=[column_mediasplit],
            right_on=["group_name"],
        )

        mediaSplitgroupeddata.sort_values(by=["value"], ascending=[False], inplace=True)
        # pdb.set_trace()
        econSplitgroupeddata = soc_data.groupby([column_econsplit, "group1"]).sum()
        econSplitgroupeddata.reset_index(inplace=True)
        econSplitgroupeddata["value"] = econSplitgroupeddata["value"].astype(float)
        econ_group_order = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_orders(column_econsplit)
        )
        econSplitgroupeddata = econSplitgroupeddata.merge(
            econ_group_order,
            how="inner",
            left_on=[column_econsplit],
            right_on=["group_name"],
        )

        econSplitgroupeddata.sort_values(by=["value"], ascending=[False], inplace=True)

        highlevel_wc_data = getWaterfallChartData(
            base=None,
            incremental={
                "names": highLevelgroupeddata[column_highlevel].values,
                "values": highLevelgroupeddata["value"].values,
            },
            total={"name": "Total", "value": 0},
            start_point=0,
            add_gap=False,
            round_digits=4,
        )
        control_wc_data = getWaterfallChartData(  # changed getwaterfallchartdatanew func
            base=None,
            incremental={
                "names": controlSplitgroupeddata[column_controlsplit].values,
                "values": controlSplitgroupeddata["value"].values,
                # "groups": controlSplitgroupeddata["group1"].values,
            },
            total={"name": "Control Total", "value": 0},
            start_point=0,
            add_gap=False,
            round_digits=4,
        )
        media_wc_data = getWaterfallChartData(
            base=None,
            incremental={
                "names": mediaSplitgroupeddata[column_mediasplit].values,
                "values": mediaSplitgroupeddata["value"].values,
            },
            total={"name": "Base Total", "value": 0},
            start_point=0,
            add_gap=False,
            round_digits=4,
        )

        econ_wc_data = getWaterfallChartData(
            base=None,
            incremental={
                "names": econSplitgroupeddata[column_econsplit].values,
                "values": econSplitgroupeddata["value"].values,
            },
            total={"name": "Marketing Total", "value": 0},
            start_point=0,
            add_gap=False,
            round_digits=4,
        )

        return {
            "highlevel": highlevel_wc_data,
            "controlsplit": control_wc_data,
            "mediasplit": media_wc_data,
            "econsplit": econ_wc_data,
        }

    def get_tree_table_headers(self, scenarios, periods):
        s1 = scenarios[0]
        s2 = scenarios[1]
        headers = []
        for period in periods:
            colsObj1 = {}
            colsObj1["title"] = str(s1) + "<br>" + period
            colsObj1["key"] = period + "_" + str(scenarios[0])
            headers.append(colsObj1)
            if scenarios[0] != scenarios[1]:
                colsObj2 = {}
                colsObj2["title"] = str(s2) + "<br>" + period
                colsObj2["key"] = period + "_" + str(scenarios[1])
                headers.append(colsObj2)
        colObj3 ={}
        colObj3["title"]="Change"
        colObj3["key"]="percent"
        headers.append(colObj3)
        return {
            "outcome1": headers,
            "outcome2": headers,
            # "O_NTFHH_CNT": headers,
            # "TOTAL_ASSET_IN": headers,
        }

    def due_to_analysis(self, request_data):
        period_type = request_data["period_type"]
        year_2 = request_data["year_1"]
        year_1 = request_data["year_2"]
        period_2 = request_data["period_1"]
        period_1 = request_data["period_2"]
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
        else:
            fmt_period_2 = request_data["period_1"].replace("H", "").replace("Q", "")
            fmt_period_1 = request_data["period_2"].replace("H", "").replace("Q", "")
        scenario_2 = int(request_data["year_1"])
        scenario_1 = int(request_data["year_2"])
        selected_node = int(request_data["node"])
        customer_list = ["outcome2", "outcome1"]
        customer_names = {
            "outcome2": "outcome2",
            # "O_NTFHH_CNT": "NTF_HH_Count",
            "outcome1": "outcome1",
        }

        media_hierarchy = pd.DataFrame.from_records(self.reporting_dao.touchpoints())

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
        selected_node_names = media_hierarchy[
            media_hierarchy["node_id"] == selected_node
        ]["leaf_nodes"].reset_index(drop=True)[0]

        chart_data = {}
        for customer in customer_list:
            # Read allocation table
            allocation_period_1 = pd.DataFrame.from_records(
                self.reporting_dao.fetch_allocation_period(
                    scenario_1, scenario_2, period_type, fmt_period_1, customer
                )
            )
            allocation_period_1["allocation"] = allocation_period_1[
                "allocation"
            ].astype(float)
            allocation_period_2 = pd.DataFrame.from_records(
                self.reporting_dao.fetch_allocation_period(
                    scenario_2, scenario_1, period_type, fmt_period_2, customer
                )
            )
            allocation_period_2["allocation"] = allocation_period_2[
                "allocation"
            ].astype(float)
            new_spend = pd.DataFrame.from_records(
                self.reporting_dao.fetch_spends(scenario_1, scenario_2, period_type)
            )
            new_spend["spend_value"] = new_spend["spend_value"].astype(float)
            old_spend = pd.DataFrame.from_records(
                self.reporting_dao.fetch_spends(scenario_2, scenario_1, period_type)
            )
            old_spend["spend_value"] = old_spend["spend_value"].astype(float)
            node_data = pd.DataFrame.from_records(self.reporting_dao.fetch_node_data())

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
                axis_label_start = period_2 + "-Year"
                axis_label_end = period_1 + "-Year"
            else:
                axis_label_start = year_2 + "-" + period_2
                axis_label_end = year_1 + "-" + period_1

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

    def get_all_soc_data(self, request_data):
        result = pd.DataFrame()
        year1 = scenario_1 = int(request_data["year1"]) or 1
        year2 = scenario_2 = int(request_data["year2"]) or 2
        period_type = request_data["period_type"] or "year"
        quarter1 = ""
        quarter2 = ""
        month1 = ""
        month2 = ""
        halfyear1 = ""
        halfyear2 = ""
        if period_type == "quarter":
            quarter1 = request_data["quarter1"]
            quarter2 = request_data["quarter2"]
            # scenario_1 = self.reporting_dao.get_scenario_by_period(
            #     scenario_1, quarter1, "", period_type
            # )[0]["scenario_id"]
            # scenario_2 = self.reporting_dao.get_scenario_by_period(
            #     scenario_2, quarter2, "", period_type
            # )[0]["scenario_id"]
        elif period_type == "month":
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
            month1 = request_data["month1"]
            month2 = request_data["month2"]
            # scenario_1 = self.reporting_dao.get_scenario_by_period(
            #     scenario_1, "", month1, period_type
            # )[0]["scenario_id"]
            # scenario_2 = self.reporting_dao.get_scenario_by_period(
            #     scenario_2, "", month2, period_type
            # )[0]["scenario_id"]
        # elif period_type == "week":
        #     month1 = request_data["month1"]
        #     month2 = request_data["month2"]
        #     week1 = request_data["week1"]
        #     week2 = request_data["week2"]
        #     scenario_1 = self.reporting_dao.get_scenario_by_period(
        #         scenario_1, "", month1, period_type
        #     )[0]["scenario_id"]
        #     scenario_2 = self.reporting_dao.get_scenario_by_period(
        #         scenario_2, "", month2, period_type
        #     )[0]["scenario_id"]
        elif period_type == "halfyear":
            halfyear1 = request_data["halfyear1"]
            halfyear2 = request_data["halfyear2"]
        column_highlevel = "group1"
        column_controlsplit = "group4"
        column_mediasplit = "group3"
        column_econsplit = "group2"

        outcome = request_data["outcome"] or "outcome2"

        if outcome == "outcome2":
            outcome = "outcome2"
        elif outcome == "outcome1":
            outcome = "outcome1"
        reporting_groups = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_by_nodes()
        )

        # Fetch SOC data from SOC Table4 new_result['allocation'] = (new_result['allocation_x'] - new_result['allocation_y'])/new_result['allocation_x'].
        s1_results = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_temp(
                scenario_1,
                scenario_2,
                outcome,
                period_type,
                quarter1,
                month1,
                halfyear1,
            )
        )
        s1_results["allocation"] = s1_results["allocation"].astype(float)
        s2_results = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_allocations_temp(
                scenario_2,
                scenario_1,
                outcome,
                period_type,
                quarter2,
                month2,
                halfyear2,
            )
        )
        s2_results["allocation"] = s2_results["allocation"].astype(float)
        soc_data = ReportingHandler().getSourceOfChange(s1_results, s2_results)
        if soc_data.empty:
            return "Data Not Found"
        soc_data = soc_data.merge(reporting_groups, how="inner", on="node_name")
        highLevelgroupeddata = soc_data.groupby(
            ["variable_type", column_highlevel]
        ).sum()
        highLevelgroupeddata.reset_index(inplace=True)
        highLevelgroupeddata["value"] = highLevelgroupeddata["value"].astype(float)
        highlevel_group_orders = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_orders(column_highlevel)
        )
        highLevelgroupeddata = highLevelgroupeddata.merge(
            highlevel_group_orders,
            how="inner",
            left_on=[column_highlevel],
            right_on=["group_name"],
        )
        highLevelgroupeddata.sort_values(by=["value"], ascending=[False], inplace=True)

        controlSplitgroupeddata = soc_data.groupby(
            [column_controlsplit, "group1"]
        ).sum()
        controlSplitgroupeddata.reset_index(inplace=True)
        controlSplitgroupeddata["value"] = controlSplitgroupeddata["value"].astype(
            float
        )
        control_group_order = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_orders(column_controlsplit)
        )
        controlSplitgroupeddata = controlSplitgroupeddata.merge(
            control_group_order,
            how="inner",
            left_on=[column_controlsplit],
            right_on=["group_name"],
        )
        controlSplitgroupeddata.sort_values(
            by=["order2", "value"], ascending=[True, False], inplace=True
        )

        mediaSplitgroupeddata = soc_data.groupby([column_mediasplit, "group1"]).sum()
        mediaSplitgroupeddata.reset_index(inplace=True)
        mediaSplitgroupeddata["value"] = mediaSplitgroupeddata["value"].astype(float)
        media_group_order = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_orders(column_mediasplit)
        )
        mediaSplitgroupeddata = mediaSplitgroupeddata.merge(
            media_group_order,
            how="inner",
            left_on=[column_mediasplit],
            right_on=["group_name"],
        )

        mediaSplitgroupeddata.sort_values(by=["value"], ascending=[False], inplace=True)

        econSplitgroupeddata = soc_data.groupby([column_econsplit, "group1"]).sum()
        econSplitgroupeddata.reset_index(inplace=True)
        econSplitgroupeddata["value"] = econSplitgroupeddata["value"].astype(float)
        econ_group_order = pd.DataFrame.from_records(
            self.reporting_dao.get_reporting_groups_orders(column_econsplit)
        )
        econSplitgroupeddata = econSplitgroupeddata.merge(
            econ_group_order,
            how="inner",
            left_on=[column_econsplit],
            right_on=["group_name"],
        )

        econSplitgroupeddata.sort_values(by=["value"], ascending=[False], inplace=True)

        if request_data["chart_type"] == "highlevel":
            group_name = column_highlevel
            df = highLevelgroupeddata
            total_group_name = "Total"
        elif request_data["chart_type"] == "mediasplit":
            group_name = column_mediasplit
            df = mediaSplitgroupeddata
            total_group_name = "Base Total"
        elif request_data["chart_type"] == "econsplit":
            group_name = column_econsplit
            df = econSplitgroupeddata
            total_group_name = "Marketing Total"
        else:
            group_name = column_controlsplit
            df = controlSplitgroupeddata
            total_group_name = "Control Total"

        result[group_name] = df[group_name].values
        result["value"] = df["value"].values
        total = pd.DataFrame(pd.DataFrame(result.sum()).transpose())
        total.loc[0][0] = total_group_name
        result = pd.concat([result, total]).reset_index(drop=True)
        result.columns = ["Group", "Overall"]
        return result

    def fetch_data_ROMI_CPA(self, request):
        logger.info("Reporting: data preparation for ROMI and CPA is started")
        from_year = int(request["from_year"])
        to_year = int(request["to_year"])
        from_quarter = int(request["from_quarter"])
        to_quarter = int(request["to_quarter"])
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
        }
        # get the allocations for the year
        allocation_df = pd.DataFrame.from_records(
            self.reporting_dao.get_allocations_for_cpa_romi(from_year, to_year)
        )
        allocation_df["value"] = allocation_df["value"].astype(float)
        if not allocation_df.empty:
            query_result_wide = pd.pivot_table(
                allocation_df,
                values="value",
                index=["node_name", "geo", "year", "halfyear", "quarter", "month"],
                columns="outcome",
            )
        else:
            return final
        # get the spends for the year
        spend = pd.DataFrame.from_records(
            self.reporting_dao.get_scenario_spend_romi_cpa(
                from_year, to_year, period_type
            )
        )
        spend["spend_value"] = spend["spend_value"].astype(float)
        # Cannot rectify this issue
        data = query_result_wide.merge(
            spend,
            on=["node_name", "geo", "year", "halfyear", "quarter", "month"],
            how="left",
        ).fillna(0)
        media_hierarchy = pd.DataFrame.from_records(
            self.reporting_dao.touchpoints()
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
            ].values
            leaf_nodes = []
            for i in media_leaf_nodes:
                for j in eval(i):
                    leaf_nodes.append(j)
            # leaf_nodes = eval(media_leaf_nodes)
            media_data = data[data["node_name"].isin(leaf_nodes)]
        media_data["outcome1"] = media_data["outcome1"].fillna(0)
        media_data["spend_value"] = media_data["spend_value"].fillna(0)
        media_data["outcome2"] = media_data["outcome2"].fillna(0)
        # media_data = pd.merge(media_data, media_hierarchy)
        media_data = pd.merge(media_data, media_hierarchy, how="inner", on=None, validate="many_to_many")


        no_of_years = to_year - from_year + 1

        # iterate for number of given years between from and to years
        for year in range(no_of_years):
            current_year = from_year + year
            row = {}
            #  get the total year data for each year
            if period_type == "year":
                data = media_data[media_data.year.eq(current_year)].sum()
                row["coutcome1"] = data["spend_value"] / data["outcome1"]
                row["coutcome2"] = data["spend_value"] / data["outcome2"]
                row["outcome1"] = data["outcome1"]
                row["outcome2"] = data["outcome2"]
                row["year"] = current_year
                row["spend"] = data["spend_value"]
                row["total_assets"] = row["coutcome1"] + row["csu"]
                if data["spend_value"] == 0.0:
                    row["coutcome1"] = 0
                    row["coutcome2"] = 0
                    row["total_assets"] = 0
                final["year"].append(row)
                final["year_labels"].append(row["year"])

            # get the quarter data for the each particular year
            elif period_type == "quarter":
                # group the data by quarter for each year
                data = (
                    media_data[media_data.year.eq(current_year)]
                    .groupby(by="quarter", as_index=False)
                    .sum()
                )
                for quarter_index in range(len(data)):
                    row = {}
                    individual_quarter_data = data.iloc[quarter_index]

                    # if from_year and to_year are same, then get the quarter data for same year
                    if from_year == to_year:
                        if (
                            current_year == from_year
                            and from_quarter <= quarter_index + 1 <= to_quarter
                        ):
                            row["coutcome1"] = round(
                                individual_quarter_data["spend_value"]
                                / individual_quarter_data["outcome1"],
                                4,
                            )
                            row["coutcome2"] = round(
                                individual_quarter_data["spend_value"]
                                / individual_quarter_data["outcome2"],
                                4,
                            )
                            row["outcome2"] = individual_quarter_data["outcome2"]
                            row["outcome1"] = individual_quarter_data["outcome1"]
                            row["year"] = current_year
                            row["spend"] = individual_quarter_data["spend_value"]
                            row["quarter"] = individual_quarter_data["quarter"]
                            row["total_assets"] = row["coutcome1"] + row["coutcome2"]

                            if individual_quarter_data["spend_value"] == 0.0:
                                row["coutcome1"] = 0
                                row["coutcome2"] = 0
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
                            (
                                current_year == from_year
                                and quarter_index + 1 >= from_quarter
                            )
                            or (current_year != from_year and current_year != to_year)
                            or (
                                current_year == to_year
                                and quarter_index + 1 <= to_quarter
                            )
                        ):
                            row["coutcome1"] = round(
                                individual_quarter_data["spend_value"]
                                / individual_quarter_data["outcome1"],
                                4,
                            )
                            row["coutcome2"] = round(
                                individual_quarter_data["spend_value"]
                                / individual_quarter_data["outcome2"],
                                4,
                            )
                            row["outcome1"] = individual_quarter_data["outcome1"]
                            row["outcome2"] = individual_quarter_data["outcome2"]
                            row["year"] = current_year
                            row["spend"] = individual_quarter_data["spend_value"]
                            row["quarter"] = individual_quarter_data["quarter"]
                            row["total_assets"] = row["coutcome2"] + row["coutcome1"]

                            if individual_quarter_data["spend_value"] == 0.0:
                                row["coutcome2"] = 0
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
                # group the data by month for each year
                data = (
                    media_data[media_data.year.eq(current_year)]
                    .groupby(by="month", as_index=False)
                    .sum()
                )
                for monthly_index in range(len(data)):
                    row = {}
                    individual_month_data = data.iloc[monthly_index]
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
                    # if from_year and to_year are same, then get the month data for same year
                    if from_year == to_year:
                        if (
                            current_year == from_year
                            and from_month <= monthly_index + 1 <= to_month
                        ):
                            row["coutcome1"] = round(
                                individual_month_data["spend_value"]
                                / individual_month_data["outcome1"],
                                4,
                            )
                            row["coutcome2"] = round(
                                individual_month_data["spend_value"]
                                / individual_month_data["outcome2"],
                                4,
                            )
                            row["outcome1"]= individual_month_data["outcome1"]
                            row["outcome2"]= individual_month_data["outcome2"]
                            row["year"] = current_year
                            row["spend"] = individual_month_data["spend_value"]
                            row["month"] = individual_month_data["month"]
                            row["total_assets"] = row["coutcome1"] + row["coutcome2"]

                            if individual_month_data["spend_value"] == 0.0:
                                row["coutcome1"] = 0
                                row["coutcome2"] = 0
                                row["total_assets"] = 0
                                # row["cpa"] = 0
                            final["month"].append(row)
                            final["month_labels"].append(
                                monthly[int(row["month"])] + "'" + str(current_year)[2:]
                            )  # Q1'2018

                    # if from_year and to_year are different, get the month data for all the given years between from and to months
                    else:
                        if (
                            (
                                current_year == from_year
                                and monthly_index + 1 >= from_month
                            )
                            or (current_year != from_year and current_year != to_year)
                            or (
                                current_year == to_year
                                and monthly_index + 1 <= to_month
                            )
                        ):
                            row["coutcome1"] = round(
                                individual_month_data["spend_value"]
                                / individual_month_data["outcome1"],
                                4,
                            )
                            row["coutcome2"] = round(
                                individual_month_data["spend_value"]
                                / individual_month_data["outcome2"],
                                4,
                            )
                            row["outcome1"]= individual_month_data["outcome1"]
                            row["outcome2"]= individual_month_data["outcome2"]
                            row["year"] = current_year
                            row["spend"] = individual_month_data["spend_value"]
                            row["month"] = individual_month_data["month"]
                            row["total_assets"] = row["coutcome1"] + row["coutcome2"]

                            if individual_month_data["spend_value"] == 0.0:
                                row["coutcome1"] = 0
                                row["coutcome2"] = 0
                                row["total_assets"] = 0
                                row["cpa"] = 0
                            final["month"].append(row)
                            final["month_labels"].append(
                                monthly[int(row["month"])] + "'" + str(current_year)[2:]
                            )

        logger.info("Reporting: data preparation for ROMI and CPA is completed")
        return final

    def download_marginal_return_curves_data(self, request_data):
        nodes = json.loads(request_data["nodes"])
        scenario_id = ""
        logger.info(
            "Reporting: data preparation for marginal return curves download is started"
        )
        if len(nodes) == 0:
            nodes = [2002, 2003, 2004, 2005, 2006]
        df = pd.DataFrame.from_records(
            self.reporting_dao.get_marginal_return_curves_download_data(
                nodes, scenario_id
            )
        )
        df = df.rename(columns={"value":"Value","value_change":"Value_Change"})
        df["spend_change_pct"] = df["spend_change_pct"].round(2).astype("float")

        # Adding Total Assets to output
        df_total = df[df["outcome"] != "O_NTFHH_CNT"]
        df_total = (
            df_total.groupby(
                ["node_id", "node_display_name", "spend_change", "spend_change_pct"]
            )[["Value", "Value_Change"]]
            .sum()
            .reset_index()
        )
        df_total["outcome"] = "TOTAL"
        df = pd.concat([df, df_total])

        marginal_return_curves_pivot = pd.pivot_table(
            df,
            values=["Value", "Value_Change"],
            index=["node_display_name", "spend_change", "spend_change_pct"],
            columns="outcome",
        )
        marginal_return_curves_pivot.reset_index(inplace=True, drop=False)

        # Output format for the excel file
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
        output_file = "Marginal_Return_Curves" + ".xlsx"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            wb = writer.book
            fmt_number = wb.add_format({"num_format": number_formats["number"]})
            fmt_dollar = wb.add_format({"num_format": "$ #,##0"})

            # Marginal return curve excel Table
            curr_sheetname = "Return_Curve_Data"
            marginal_return_curves_pivot.to_excel(writer, sheet_name=curr_sheetname)
            ws2 = writer.sheets[curr_sheetname]
            ws2.set_column("B:C", 20, fmt_number)  # node_display_name and spend change
            ws2.set_column("C:C", 20, fmt_dollar)  # node_display_name and spend change
            ws2.set_column("D:D", 20)  # spend change pct
            ws2.set_column("E:L", 20, fmt_number)  # value and value change
            # Formatting O_EXASSET_IN, O_NTFASSET_IN, O_TOTALASSET_IN columns
            ws2.set_column("E:F", 20, fmt_dollar)
            ws2.set_column("H:J", 20, fmt_dollar)
            ws2.set_column("L:L", 20, fmt_dollar)
            ws2.set_zoom(90)

            # writer.close()

        logger.info(
            "Reporting: data preparation for marginal return curves download is ended"
        )

        return output
