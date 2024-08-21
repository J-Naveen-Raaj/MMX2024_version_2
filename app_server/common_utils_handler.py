import traceback

import numpy as np
import pandas as pd
from sqlalchemy import text

from app_server.common_utils_dao import UtilsDAO
from app_server.custom_logger import get_logger
from app_server.database_handler import DatabaseHandler
from app_server.optimization_dao import OptimizationDAO

logger = get_logger(__name__)


class UtilsHandler(object):
    def __init__(self):
        self.db_conn = DatabaseHandler().get_database_conn()
        self.conn_without_factory = (
            DatabaseHandler().get_database_conn_without_factory()
        )
        self.utils_dao = UtilsDAO(self.db_conn)
        self.optimization_dao = OptimizationDAO(self.db_conn)
        self.df = pd.DataFrame()

    # def fetch_scenario_list(self):
    #     scenario_list = self.utils_dao.get_scenario_list()
    #     return scenario_list

    def get_period_range(self):
        timeperiod = self.utils_dao.get_period_range()
        time_period = pd.DataFrame.from_records(timeperiod)
        time_period = time_period.sort_values(by=["year", "month"])
        time_frame = {}
        d = {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sept",
            10: "Oct",
            11: "Nov",
            12: "Dec",
        }
        time_frame["min_date"] = (
            str(time_period.iloc[0]["year"])
            + "-"
            + str(d[time_period.iloc[0]["month"]])
        )
        time_frame["max_date"] = (
            str(time_period.iloc[-1]["year"])
            + "-"
            + str(d[time_period.iloc[-1]["month"]])
        )
        return time_frame

    def fetch_media_hierarchy_touchpoint(self):
        scenario_list = self.utils_dao.get_media_hierarchy_touchpoint()
        return scenario_list

    def getPeriodList(self, x):  # Higher time period_name's
        if x == "monthly":
            return [
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
        if x == "quarterly":
            return ["Q1", "Q2", "Q3", "Q4"]
        if x == "halfyearly":
            return ["H1", "H2"]
        if x == "yearly":
            return ["Year"]

    def ParentNodeAggegation(self, node, d, period_name):
        self.df.loc[
            (self.df["node_id"] == node) & (self.df["period_name"] == period_name),
            "spend_value",
        ] = (
            self.df.loc[
                (self.df["node_id"] == node) & (self.df["period_name"] == period_name),
                "spend_value",
            ]
            + d
        )

        if (
            len(
                self.df[
                    (self.df["node_id"] == node)
                    & (self.df["period_name"] == period_name)
                ]["parent_node_id"]
            )
            > 0
        ):
            if (
                self.df[
                    (self.df["node_id"] == node)
                    & (self.df["period_name"] == period_name)
                ]["parent_node_id"].iloc[0]
                == 0
            ):  # change to null or nan
                return
            else:
                return self.ParentNodeAggegation(
                    self.df[
                        (self.df["node_id"] == node)
                        & (self.df["period_name"] == period_name)
                    ]["parent_node_id"].iloc[0],
                    d,
                    period_name,
                )
        else:
            return self.df

    def Parentnodechange(
        self, node, period_name
    ):  # for a given node&period_name changes Parent node value
        logger.info("node :%s", node)
        df_copy = pd.DataFrame()
        df_copy = self.df.copy()

        rows1 = df_copy[
            (df_copy["parent_node_id"] == node) & (df_copy["node_name"].isnull())
        ]
        rows = rows1.copy()
        rows["period_name"] = period_name
        rows["spend_value"] = 0

        self.df = self.df.append(rows)
        self.df.loc[
            (self.df["node_id"] == node) & (self.df["period_name"] == period_name),
            "period_name",
        ] = period_name

        if (
            len(
                self.df[
                    (self.df["parent_node_id"] == node)
                    & (self.df["period_name"] == period_name)
                ]
            )
            > 0
        ) & (
            self.df[
                (self.df["parent_node_id"] == node)
                & (self.df["period_name"] == period_name)
            ]["node_name"]
            .isnull()
            .sum()
            == 0
        ):
            total_spend = self.df[
                (self.df["parent_node_id"] == node)
                & (self.df["period_name"] == period_name)
            ]["spend_value"].sum()

            self.df.loc[
                (self.df["node_id"] == node) & (self.df["period_name"] == period_name),
                "spend_value",
            ] = total_spend

            if node != 0:
                parent_node = self.df[
                    (self.df["node_id"] == node)
                    & (self.df["period_name"] == period_name)
                ]["parent_node_id"].iloc[0]
                self.ParentNodeAggegation(parent_node, total_spend, period_name)
            return self.df
        else:
            nodes = self.df[
                (self.df["parent_node_id"] == node)
                & (self.df["period_name"] == period_name)
                & (self.df["node_name"].isnull())
            ]["node_id"].unique()

            for node in nodes:
                self.Parentnodechange(node, period_name)
            return self.df

    def insert_dataframe_to_mssql(self, df, table):
        try:
            logger.info("Started dataframe inserts to database...")
            cur = self.conn_without_factory
            # trans = cur.begin()
            placeholders = ", ".join([":" + col for col in df.columns])
            columns = ", ".join(df.columns)
            query = text(f"INSERT INTO {table} ({columns}) VALUES({placeholders})")

            # Execute the SQL query with parameter binding
            cur.execute(query, df.to_dict(orient="records"))
            # cur.executemany(query, data)
            # self.conn_without_factory.commit()
            # trans.commit()
            logger.info("Completed dataframe inserts to database table %s", table)
        except Exception as e:
            print(traceback.format_exc())
            logger.exception("Exception in dataframe inserts %s" % str(e))


