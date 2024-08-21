# coding=utf-8
import pandas as pd


class UtilsDAO(object):
    """
    Utils functions that are used in common
    """

    def __init__(self, conn):
        self.conn = conn

    def get_scenario_list(self):
        query = "SELECT * FROM spend_scenario order by scenario_id;"
        return self.conn.processquery(query)
    def get_scenarios(self):
        query = "SELECT * FROM scenarios order by id;"
        return self.conn.processquery(query)

    def get_media_hierarchy_touchpoint(self):
        query = "SELECT m.*,t.* FROM media_hierarchy as m left join media_touchpoints as t on t.node_id = m.node_id;"
        return self.conn.processquery(query)

    def get_select_touchpoints(self):
        query = "SELECT * FROM select_touchpoints;"
        return self.conn.processquery(query)
    def get_optimization_scenario(self):
        query = "SELECT * FROM optimization_scenario;"
        return self.conn.processquery(query)
    def get_period_range(self):
        query = "SELECT * FROM reporting_allocations_temp;"
        return self.conn.processquery(query)

