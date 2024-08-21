import traceback

import pandas as pd

from app_server.custom_logger import get_logger
from app_server.database_handler import DatabaseHandler
from app_server.maintenance_dao import MaintenanceDAO

logger = get_logger(__name__)


class MaintenanceHandler(object):

    def __init__(self):
        self.db_conn = DatabaseHandler().get_database_conn()
        self.maintenance_dao = MaintenanceDAO(self.db_conn)

    def get_maintenance_scenario_list(self):
        try:
            maintenance_scenario_list = pd.DataFrame(
                self.maintenance_dao.get_maintenance_scenario_list()
            )
            maintenance_planner_list = pd.DataFrame(
                self.maintenance_dao.get_maintenance_planner_list()
            )

            def calculate_period_values(row):
                if row["period_type"] == "yearly":
                    return None, None
                elif row["period_type"] == "quarterly":
                    return 1, 4
                elif pd.isnull(row["period_type"]):
                    return None, None
                else:
                    return 1, 12

            maintenance_planner_list[["period_start", "period_end"]] = (
                maintenance_planner_list.apply(
                    calculate_period_values, axis=1, result_type="expand"
                )
            )
            maintenance_scenario_list["category"] = "Optimized"
            maintenance_planner_list.rename(
                columns={"year": "period_year", "name": "scenario_name"}, inplace=True
            )
            maintenance_planner_list["status"] = "Completed"
            maintenance_planner_list.loc[:, "category"] = "Planner"
            appended_df = pd.concat(
                [maintenance_planner_list, maintenance_scenario_list],
                ignore_index=True,
                sort=False,
            )
            appended_df.fillna("-", inplace=True)
            appended_dict = appended_df.to_dict(orient="records")
            maintenance_list = sorted(
                appended_dict, key=lambda x: x["created_on"], reverse=True
            )
            return maintenance_list
        except Exception as e:
            print(traceback.format_exc())
            logger.exception(
                "Exception in method get_maintenance_scenario_list %s", str(e)
            )

    def get_individual_basespends(self, request_data):
        results = self.maintenance_dao.fetch_individual_basespends(
            int(request_data["scenario_id"])
        )
        return results

    def get_scenario_outcome(self, request_data):
        get_id = self.maintenance_dao.get_scenario_id(request_data["scenario_name"])[0][
            "scenario_id"
        ]
        base_id = self.maintenance_dao.get_scenario_id(request_data["base_scenario"])[
            0
        ]["scenario_id"]
        results1 = pd.DataFrame.from_records(
            self.maintenance_dao.fetch_scenario_outcome(get_id)
        )
        results2 = pd.DataFrame.from_records(
            self.maintenance_dao.fetch_scenario_outcome(base_id)
        )
        results2.rename(
            columns={
                "optimized_spend": "base_optimized_spend",
                "optimized_value": "base_optimized_value",
                "scenario_id": "base_scenario_id",
            },
            inplace=True,
        )
        results1 = pd.merge(
            results1,
            results2,
            on=[
                "outcome",
                "channel_name",
                "tactic_name",
                "segment",
                "quarter",
                "month",
                "node_name",
            ],
            how="inner",
        )
        pivot_df = results1.pivot_table(
            values=[
                "optimized_spend",
                "optimized_value",
                "base_optimized_spend",
                "base_optimized_value",
            ],
            index=["quarter", "month", "node_name", "channel_name", "tactic_name"],
            columns="outcome",
            aggfunc="first",
        ).reset_index()
        pivot_df.columns = [
            f"{col[0]}_{col[1]}" if col[1] else col[0] for col in pivot_df.columns
        ]
        pivot_df = pivot_df.drop(
            columns=["optimized_spend_outcome2", "base_optimized_spend_outcome2"]
        )
        # Rename the 'optimized_spend_O_FTBS' column to 'optimized_spend'
        pivot_df = pivot_df.rename(
            columns={
                "optimized_spend_outcome1": "optimized_spend",
                "node_name": "variable_name",
                "base_optimized_spend_outcome1": "base_spend",
            }
        )
        pivot_df["scenario_id"] = request_data["scenario_id"]
        pivot_df = pivot_df[
            ["scenario_id"] + [col for col in pivot_df.columns if col != "scenario_id"]
        ]
        pivot_df["change_spend"] = -(
            pivot_df["optimized_spend"] - pivot_df["base_spend"]
        )
        pivot_df["change_outcome1"] = -(
            pivot_df["optimized_value_outcome1"] - pivot_df["base_optimized_value_outcome1"]
        )
        pivot_df["change_outcome2"] = -(
            pivot_df["optimized_value_outcome2"]
            - pivot_df["base_optimized_value_outcome2"]
        )
        pivot_df = pivot_df.rename(columns={'base_optimized_value_outcome1': 'base_outcome1','base_optimized_value_outcome2':'base_outcome2'})

        return pivot_df

    def get_scenario_outcome_planner(self, request_data):
        get_id = self.maintenance_dao.get_scenario_id(request_data["scenario_name"])[0][
            "scenario_id"
        ]
        results1 = pd.DataFrame.from_records(
            self.maintenance_dao.fetch_scenario_outcome(get_id)
        )
        pivot_df = results1.pivot_table(
            values=["optimized_spend", "optimized_value"],
            index=["quarter", "month", "node_name", "channel_name", "tactic_name"],
            columns="outcome",
            aggfunc="first",
        ).reset_index()
        pivot_df.columns = [
            f"{col[0]}_{col[1]}" if col[1] else col[0] for col in pivot_df.columns
        ]
        pivot_df = pivot_df.drop(columns=['optimized_spend_outcome2'])
        # Rename the 'optimized_spend_outcome1' column to 'optimized_spend'
        pivot_df = pivot_df.rename(columns={'optimized_spend_outcome1': 'spend','node_name':'variable_name','optimized_value_outcome1':'outcome1','optimized_value_outcome2':'outcome2'})
        pivot_df['scenario_id'] = request_data['scenario_id']
        pivot_df = pivot_df[['scenario_id'] + [col for col in pivot_df.columns if col != 'scenario_id']]

        return pivot_df


    def delete_optimized_scenario(self, request_data):
        logger.info("In delete_optimized_scenario method")
        self.maintenance_dao.delete_from_optimization_scenario(
            request_data["optimization_scenario_id"]
        )
        logger.info("delete_from_individual_spend ... ")
        self.maintenance_dao.delete_from_individual_spend(
            request_data["optimization_scenario_id"]
        )
        logger.info("delete_from_scenario_table ...")
        get_id = self.maintenance_dao.get_scenario_id(request_data["scenario_name"])
        if len(get_id) != 0:
            self.maintenance_dao.delete_from_scenario_table(
                get_id[0]["scenario_id"], "spend_scenario"
            )
            self.maintenance_dao.delete_from_scenario_table(
                get_id[0]["scenario_id"], "spend_scenario_details"
            )
            self.maintenance_dao.delete_from_scenario_table(
                get_id[0]["scenario_id"], "scenario_outcome"
            )
        logger.info("delete_from_optimized_table ...")
        get_id_scenario = self.maintenance_dao.get_scenario_name(
            request_data["scenario_name"], "Optimized"
        )
        if len(get_id_scenario) != 0:
            self.maintenance_dao.delete_from_optimization_table(
                get_id_scenario[0]["id"], "scenarios", "id"
            )
            self.maintenance_dao.delete_from_optimization_table(
                get_id_scenario[0]["id"],
                "optimization_spend_scenario_data",
                "scenario_id",
            )
            self.maintenance_dao.delete_from_optimization_table(
                get_id_scenario[0]["id"], "optimization_scenario_outcome", "ScenarioId"
            )
        maintenance_scenario_list = self.get_maintenance_scenario_list()
        maintenance_scenario_list = sorted(
            maintenance_scenario_list, key=lambda x: x["created_on"], reverse=True
        )

        return maintenance_scenario_list

    def delete_scenario(self, request_data):
        logger.info("delete_from_scenario_table ...")
        get_id = self.maintenance_dao.get_scenario_id(request_data["scenario_name"])
        if len(get_id) != 0:
            self.maintenance_dao.delete_from_scenario_table(
                get_id[0]["scenario_id"], "spend_scenario"
            )
            self.maintenance_dao.delete_from_scenario_table(
                get_id[0]["scenario_id"], "spend_scenario_details"
            )
            self.maintenance_dao.delete_from_scenario_table(
                get_id[0]["scenario_id"], "scenario_outcome"
            )
        logger.info("delete_from_optimized_table ...")
        get_id_scenario = self.maintenance_dao.get_scenario_name(
            request_data["scenario_name"], "Base"
        )
        if len(get_id_scenario) != 0:
            self.maintenance_dao.delete_from_optimization_table(
                get_id_scenario[0]["id"], "scenarios", "id"
            )
            self.maintenance_dao.delete_from_optimization_table(
                get_id_scenario[0]["id"],
                "optimization_spend_scenario_data",
                "scenario_id",
            )
            self.maintenance_dao.delete_from_optimization_table(
                get_id_scenario[0]["id"], "optimization_scenario_outcome", "ScenarioId"
            )
        maintenance_scenario_list = self.get_maintenance_scenario_list()

        return maintenance_scenario_list
