import datetime


class ScenarioDAO(object):
    def __init__(self, conn):
        self.conn = conn

    def get_user_scenarios(self, user_id):
        query = """select distinct ss.scenario_id,ss.scenario_name ,last_updated_date
                   from spend_scenario ss
                   inner join spend_scenario_details sd on sd.scenario_id = ss.scenario_id
                   where user_id=:user_id and ss.active = 1 order by last_updated_date asc"""
        arguments = {"user_id": user_id}

        return self.conn.processquery(query, arguments)
    def get_convergence_scenarios(self):
        query = """select opt.name from optimization_scenario opt where status = 'No solution found'"""
        return self.conn.processquery(query)

    # def validation(self, scenario_id):
    #     query = """
    #         select node_id,
    #             period_type,
    #             sum(spend_value) as total_spend_value
    #         from spend_scenario_details
    #         where scenario_id = :scenario_id
    #         group by 1,2
    #         having total_spend_value > 0
    #     """
    #     arguments = [{"scenario_id": scenario_id}]
    #     return self.conn.processquery(query, arguments)

    def delete_spend_scenario_details(self, scenario_id):
        query = """
        delete from spend_scenario_details where scenario_id = :scenario_id
        """
        arguments = [{"scenario_id": int(scenario_id)}]
        return self.conn.processqueryinsert(query, arguments)

    def get_scenarios_from_outcome(self):
        query = (
            "select distinct s.scenario_id,s.scenario_name from spend_scenario s "
            "inner join scenario_outcome so on so.scenario_id = s.scenario_id where s.active = 1 "
            "order by s.scenario_id"
        )
        return self.conn.processquery(query)

    def get_media_touchpoints(self):
        query = (
            "SELECT node_id,node_name, parent_node_id, node_display_name, node_description as node_ref_name, node_seq,leaf_nodes "
            "FROM select_touchpoints mh "
        )
        return self.conn.processquery(query)

    def get_data_for_scenario_id(self, scenario_id, period_type):
        query = (
            "select DISTINCT parent_node_id as node_parent, sd.node_id,mh.node_name, node_display_name as node_disp_name, "
            "node_description as node_ref_name, node_seq,leaf_nodes,period_type,period_name,spend_value "
            "from spend_scenario_details sd "
            "inner join select_touchpoints mh on sd.node_id=mh.node_id "
            "where sd.scenario_id=:scenario_id and sd.period_type=:period_type "
        )

        #   "inner join models m on m.version_id = mh.version_id and m.active = 1 " \
        arguments = {"scenario_id": scenario_id, "period_type": period_type}
        print(query, arguments)
        return self.conn.processquery(query, arguments)

    def get_data_for_scenario_name(self, scenario_name, period_type):
        query = (
            "select parent_node_id as node_parent, sd.node_id, node_display_name as node_disp_name, node_description as node_ref_name, node_seq, "
            "period_type,period_name,spend_value "
            "from spend_scenario ss join spend_scenario_details sd on ss.scenario_id=sd.scenario_id "
            "inner join media_hierarchy mh on sd.node_id=mh.node_id "
            "inner join models m on m.version_id = mh.version_id and m.active = 1 "
            "where ss.scenario_name=:scenario_name and sd.period_type=:period_type and ss.active = 1"
        )

        arguments = {"scenario_name": scenario_name, "period_type": period_type}
        print(query, arguments)
        return self.conn.processquery(query, arguments)

    def create_new_scenario(
        self, scenario_name, user_id, year, period_type, spend_value
    ):
        query = (
            "INSERT INTO spend_scenario (scenario_name, scenario_notes, user_id, created_by, created_date, last_updated_by, last_updated_date,scenario_type,active,year,period_type,spend_value) "
            "VALUES (:scenario_name, :scenario_notes, :user_id, :created_by, :created_date, :last_updated_by, :last_updated_date, :scenario_type, :active,:year,:period_type,:spend_value)"
        )

        argument_list = [
            {
                "scenario_name": scenario_name,
                "scenario_notes": "adding new scenario to " + str(user_id),
                "user_id": user_id,
                "created_by": "system",
                "created_date": str(datetime.datetime.now()),
                "last_updated_by": "system",
                "last_updated_date": str(datetime.datetime.now()),
                "scenario_type": "User",
                "active": 1,
                "year": year,
                "period_type": period_type,
                "spend_value": spend_value,
            }
        ]

        return self.conn.processquery(query, argument_list, return_id=True)

    def add_new_scenario_detail(
        self, node_id, scenario_id, period_type, period_name, spend_value
    ):
        query = (
            "insert into spend_scenario_details"
            "(node_id, scenario_id, period_type, period_name, spend_value) "
            "values(:node_id, :scenario_id, :period_type, :period_name, :spend_value)"
        )
        value_spend = float(str(spend_value).replace(",", ""))
        # argument_list = (node_id, scenario_id, period_type, period_name, float(str(spend_value).replace(",", "")))
        argument_list = [
            {
                "node_id": node_id,
                "scenario_id": scenario_id,
                "period_type": period_type,
                "period_name": period_name,
                "spend_value": value_spend,
            }
        ]
        return self.conn.processquery(query, argument_list, return_id=False)

    def fetch_scenario_data_for_change_by_sid(self, scenario_id, period_name=None):
        # pdb.set_trace()
        query = (
            "select ss.scenario_id, sd.node_id, sd.period_type, sd.period_name, CAST(sd.spend_value as float) as spend_value, "
            "mh.parent_node_id as node_parent, mh.node_name, mh.node_display_name as node_disp_name, mh.node_seq, mh.node_description as node_ref_name "
            "from spend_scenario ss join spend_scenario_details sd on ss.scenario_id=sd.scenario_id "
            "join select_touchpoints mh on mh.node_id=sd.node_id "
            "where ss.scenario_id=:scenario_id and ss.active = 1"
        )
        if period_name:
            query += " and sd.period_name =:period_name"
            argument_list = [{"scenario_id": scenario_id, "period_name": period_name}]
        else:
            argument_list = [{"scenario_id": scenario_id}]
        # print(argument_list)
        return self.conn.processquery(query, argument_list)

    def get_scenario_planning_report(self, scenario_id, period_type):
        period_type_dict = {
            "qtrly": "quarterly",
            "yearly": "yearly",
            "halfyearly": "halfyearly",
            "monthly": "monthly",
            "weekly": "weekly",
        }
        query = (
            "select ssd.period_name, SUBSTR(mh.leaf_nodes, 3, length(mh.leaf_nodes)-4) as Variable_Name, mh.node_description as Variable_Description, ssd.spend_value "
            "from spend_scenario_details ssd join select_touchpoints mh on ssd.node_id = mh.node_id "
            "where ssd.scenario_id = :scenario_id and ssd.period_type = :period_type and mh.node_name != ' '"
        )
        arguments = {
            "scenario_id": scenario_id,
            "period_type": period_type_dict[period_type],
        }
        return self.conn.processquery(query, arguments)

    def get_calendar(self):
        query = "select * FROM  calendar"
        return self.conn.processquery(query)

    def get_spendvariables(self):
        query = "select * FROM spendvariables"
        return self.conn.processquery(query)

    def get_seasonality_data(self):
        query = "select * FROM seasonality"
        return self.conn.processquery(query)

    def get_controlmapping(self):
        query = "select * FROM control_mapping"
        return self.conn.processquery(query)

    def get_ad_stocks_what_if_SU(self):
        query = 'select * FROM "adstock_what_if_SIGNUPS"'
        return self.conn.processquery(query)

    def get_ad_stocks_what_if_FTB(self):
        query = 'select * FROM "adstock_what_if_FTBS"'
        return self.conn.processquery(query)

    def get_media_inflation(self):
        query = "select * FROM media_inflation"
        return self.conn.processquery(query)

    def get_min_max(self):
        query = "select * FROM min_max"
        return self.conn.processquery(query)

    def get_forecastdata(self):
        query = "select * FROM master_data"
        return self.conn.processquery(query)

    def get_datadictonary(self):
        query = "select * FROM data_dictionary"
        return self.conn.processquery(query)

    def get_model_coeff(self):
        query = "select * FROM model_coefficients"
        return self.conn.processquery(query)

    def get_year_ratio(self):
        query = "select * FROM year_ratios"
        return self.conn.processquery(query)

    def get_coefficients_merged(self):
        query = "SELECT * FROM coefficients_merged"
        query = "SELECT * FROM model_coefficients"
        return self.conn.processquery(query)

    def get_sceanarioyear(self, scenario_id):
        query = "select year FROM spend_scenario where scenario_id = :scenario_id "
        arguments = {"scenario_id": scenario_id}
        return self.conn.processquery(query, arguments)

    def get_year_name(self, scenario_name):
        query = "select year FROM spend_scenario where scenario_name = :scenario_name "
        arguments = {"scenario_name": scenario_name}
        return self.conn.processquery(query, arguments)

    def get_variable_node_mapping(self):
        query = "select * from variable_node_mapping"
        return self.conn.processquery(query)
