import datetime

import pytz


class OptimizationDAO(object):
    """ """

    def __init__(self, conn):
        self.conn = conn

    def fetch_optimization_records(self):
        """

        Returns
        -------

        """
        query = (
            "select op.id,input_file,scenario_name,output_file, log_file, submission_time,completion_time from optimization_records op "
            "inner join spend_scenario s on s.scenario_id = op.scenario_id order by submission_time desc"
        )
        return self.conn.processquery(query)

    def fetch_all_scenario_list(self):
        """

        Returns
        -------

        """
        query = "select name as scenario_name,id as scenario_id from scenarios where active = 1"
        return self.conn.processquery(query)

    def fetch_base_scenario_list(self):
        """

        Returns
        -------

        """
        query = (
            "select name as scenario_name,id as scenario_id from scenarios "
            "where scenario_type = 'Base'"
        )
        return self.conn.processquery(query)

    def fetch_base_scenario_total_budget(
        self, scenario_id, period_type="quarter", period_start=None, period_end=None
    ):
        """

        Parameters
        ----------
        scenario_id
        period_type
        period_start
        period_end

        Returns
        -------
        sum of budget from period_start to period_end

        """
        if period_start is None:
            period_start = 1
        end_mapping = {"quarter": 4, "month": 12}
        if period_end is None:
            period_end = end_mapping.get(period_type)

        query = """
            select CAST(sum(spend) as float) as total_budget
            from optimization_spend_scenario_data
            where scenario_id = :scenario_id
                and {period_type} >= :period_start
                and {period_type} <= :period_end
        """.format(
            period_type=period_type
        )
        argument_list = [
            {
                "scenario_id": scenario_id,
                "period_start": period_start,
                "period_end": period_end,
            }
        ]
        return self.conn.processquery(query, argument_list)

    def fetch_optimization_types(self):
        """

        Returns
        -------

        """
        query = "select id,name from optimization_type"
        return self.conn.processquery(query)

    def fetch_optimization_scenarios(self):
        """

        Returns
        -------

        """
        query = """
        select id,
            name
        from optimization_scenario os
        inner join spend_scenario ss on ss.scenario_name = os.name 
        where optimized_scenario_id is not null
        """
        return self.conn.processquery(query)

    def fetch_granular_level_media_touchpoints_list(self):
        """

        Returns
        -------

        """
        query = (
            "select variable_id,variable_description from variable_node_mapping vn "
            "inner join select_touchpoints m on m.node_id = vn.node_id "
            "where m.node_id < 4000 and m.node_name not like '%FLAGS%' "
        )
        return self.conn.processquery(query)

    def fetch_touchpoint_groups_list(self):
        """

        Returns
        -------

        """
        query = "select id,name from touchpoint_groups "
        return self.conn.processquery(query)

    def fetch_optimization_group_constraints(self, scenario_id):
        """

        Parameters
        ----------
        scenario_id

        Returns
        -------

        """
        query = (
            "select gc.id,t.name,gc.period,gc.constraint_type,cast(gc.value as float) as value from group_constraints gc "
            "inner join touchpoint_groups t on t.id = gc.group_id "
            "where optimization_scenario_id = :scenario_id"
        )
        argument_list = {"scenario_id": scenario_id}
        return self.conn.processquery(query, argument_list)

    def insert_optimization_scenario(self, inputs,username):
        """

        Parameters
        ----------
        inputs

        Returns
        -------

        """
        # user_timezone = inputs.get('userTimezone', 'UTC')
        user_timezone = pytz.timezone('US/Pacific')
        current_time_user = datetime.datetime.now(user_timezone)
        query = (
            "insert into optimization_scenario (name,optimization_type_id,outcome_maximize,base_scenario_id,"
            "base_budget,incremental_budget,total_budget,period_year,period_start,period_end,created_on,period_type,status,username)"
            "values (:name, :optimization_type_id, :outcome_maximize, :base_scenario_id, :base_budget, :incremental_budget, :total_budget, :period_year, :period_start, :period_end, :created_on, :period_type, :status,:username)"
        )

        argument_list = {
            "name": inputs["scenario_name"],
            "optimization_type_id": inputs["scenario_type"],
            "outcome_maximize": inputs["outcome_to_maximum"],
            "base_scenario_id": inputs["base_scenario"],
            "base_budget": inputs["budget"],
            "incremental_budget": inputs["incremental_budget"],
            "total_budget": inputs["total_budget"],
            "period_year": inputs["year"],
            "period_start": inputs["period_start"],
            "period_end": inputs["period_end"],
            "period_type": inputs["period_type"],
            "created_on":  current_time_user.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Saved",
            "username": "User",
        }

        return self.conn.processquery(query, argument_list, return_id=True)

    def update_optimization_scenario_with_optimized_scenario_id(
        self, optimized_scenario_id, optimization_scenario_id, filename
    ):
        """

        Parameters
        ----------
        optimized_scenario_id
        optimization_scenario_id

        Returns
        -------

        """
        print(optimized_scenario_id, optimization_scenario_id)
        query = (
            "update optimization_scenario set optimized_scenario_id =:optimized_scenario_id,"
            "output_file = :filename where id= :optimization_scenario_id"
        )
        argument_list = [
            {
                "optimized_scenario_id": int(optimized_scenario_id),
                "filename": filename,
                "optimization_scenario_id": int(optimization_scenario_id),
            }
        ]
        return self.conn.processqueryinsert(query, argument_list)

    def update_optimization_scenario_status(self, optimization_scenario_id, status):
        """

        Parameters
        ----------
        optimization_scenario_id
        status

        Returns
        -------

        """
        query = (
            "update optimization_scenario set status =:status "
            "where id= :optimization_scenario_id"
        )
        argument_list = [
            {
                "status": status,
                "optimization_scenario_id": int(optimization_scenario_id),
            }
        ]
        return self.conn.processqueryinsert(query, argument_list)

    def fetch_optimization_scenario_status(self, optimization_scenario_id):
        """

        Parameters
        ----------
        scenario_id

        Returns
        -------

        """
        query = (
            "select status from optimization_scenario "
            "where id = :optimization_scenario_id"
        )
        argument_list = {"optimization_scenario_id": optimization_scenario_id}
        return self.conn.processquery(query, argument_list)

    def fetch_individual_basespends(self, optimization_scenario_id, period_type):
        """

        Parameters
        ----------
        optimization_scenario_id

        Returns
        -------

        """
        query = """
        select variable_name,
            variable_description,variable_category,
            CASE
                WHEN :period_type = 'month' THEN s.month
                WHEN :period_type = 'quarter' THEN s.quarter
                ELSE NULL
            END AS period,
            CAST(SUM(spend) as float) as spend
        from optimization_spend_scenario_data s
        inner join variable_node_mapping v on v.variable_id = s.variable_id
        inner join optimization_scenario os on os.base_scenario_id = s.scenario_id
        where os.id = :optimization_scenario_id
        GROUP BY variable_name, variable_description, variable_category, period
        order by variable_description asc
        """
        argument_list = [
            {
                "optimization_scenario_id": optimization_scenario_id,
                "period_type": period_type,
            }
        ]
        return self.conn.processquery(query, argument_list)

    def fetch_included_touchpoints(self, group_id):
        """

        Parameters
        ----------
        group_id

        Returns
        -------

        """
        query = (
            "select v.variable_id,n.variable_description from touchpoint_groups g "
            "inner join touchpoint_group_variable_mapping v on v.group_id = g.id "
            "inner join variable_node_mapping n on n.variable_id = v.variable_id "
            "inner join select_touchpoints m on m.node_id = n.node_id "
            "where g.id = :group_id "
        )
        argument_list = [{"group_id": group_id}]
        return self.conn.processquery(query, argument_list)

    def create_group(self, group_name):
        """

        Parameters
        ----------
        group_name

        Returns
        -------

        """
        if self.group_exists(group_name):
            raise ValueError(f"Group with name '{group_name}' already exists.")
        query = "insert into touchpoint_groups (name) values (:group_name)"
        argument_list = {"group_name": group_name}
        return self.conn.processqueryinsert(query, argument_list, return_id=False)

    def group_exists(self, group_name):
        """
        Check if a group with the given name already exists.

        Parameters
        ----------
        group_name

        Returns
        -------
        bool
            True if the group exists, False otherwise.
        """
        query = "SELECT COUNT(*) FROM touchpoint_groups WHERE name = :group_name"
        argument_list = {"group_name": group_name}
        result = self.conn.processquery(query, argument_list)
        # If the count is greater than 0, the group exists
        if (
            result
            and isinstance(result, list)
            and len(result) > 0
            and isinstance(result[0], dict)
            and "COUNT(*)" in result[0]
        ):
            return result[0]["COUNT(*)"] > 0
        else:
            return False

    def create_new_base_scenario(self, scenario_name):
        """

        Parameters
        ----------
        scenario_name

        Returns
        -------

        """
        query = "insert into scenarios (name,scenario_type,created_on) values (:scenario_name, :scenario_type,DATETIME('now')) "
        argument_list = [{"scenario_name": scenario_name, "scenario_type": "Base"}]
        return self.conn.processquery(query, argument_list, return_id=True)

    def check_scenario_exist(self, name):
        query = "SELECT count(*) as no_of_scenario from scenarios where name = :name "
        argument_list = [{"name": name}]
        return self.conn.processquery(query, argument_list)

    def check_optimization_scenario_exist(self, name):
        query = "SELECT count(*) as no_of_scenario from optimization_scenario where name = :name "
        argument_list = [{"name": name}]
        return self.conn.processquery(query, argument_list)

    def create_new_spend_scenario(self, scenario_name,spend_scenario_year,notes="Optimized"):
        """

        Parameters
        ----------
        scenario_name

        Returns
        -------

        """
        query = (
            "insert into spend_scenario(scenario_name, scenario_notes, user_id, created_by, "
            "created_date, last_updated_by, last_updated_date, scenario_type, active, year) "
            "values (:scenario_name, :notes, :user_id, :created_by, :created_date, :last_updated_by, :last_updated_date, :scenario_type, :active, :year) "
        )

        # query = "insert into spend_scenario (scenario_name, scenario_notes, user_id, created_by) values (?, ?, ?, ?) "
        argument_list = [
            {
                "scenario_name": scenario_name,
                "notes": notes,
                "user_id": "1",
                "created_by": "app",
                "created_date": str(datetime.datetime.now()),
                "last_updated_by": "system",
                "last_updated_date": str(datetime.datetime.now()),
                "scenario_type": "User",
                "active": 1,
                "status": "saved",
                "year":spend_scenario_year
            }
        ]
        return self.conn.processqueryinsert(query, argument_list, return_id=False)

    def create_new_optimized_scenario(self, scenario_name,username):
        """

        Parameters
        ----------
        scenario_name

        Returns
        -------

        """
        user_timezone = pytz.timezone('US/Pacific')
        current_time_user = datetime.datetime.now(user_timezone)
        query = "insert into scenarios (name,scenario_type,created_on) values (:scenario_name, :scenario_type,  :created_on) "
        argument_list = [{"scenario_name": scenario_name, "scenario_type": "Optimized","created_on":  current_time_user.strftime("%Y-%m-%d %H:%M:%S")}]
        return self.conn.processqueryinsert(query, argument_list, return_id=False)

    def create_new_optimized_scenarios(self, scenario_name,username,scenario_type):
        """

        Parameters
        ----------
        scenario_name

        Returns
        -------

        """
        user_timezone = pytz.timezone('US/Pacific')
        current_time_user = datetime.datetime.now(user_timezone)
        query = "insert into scenarios (name,scenario_type,username,active,created_on) values (:scenario_name, :scenario_type, :username,1,:created_on) "
        argument_list = [
            {"scenario_name": scenario_name, "scenario_type": scenario_type, "username": username,"created_on":  current_time_user.strftime("%Y-%m-%d %H:%M:%S"),}
        ]
        return self.conn.processquery(query, argument_list, return_id=True)

    def add_group_constraint(self, request):
        """

        Parameters
        ----------
        request

        Returns
        -------

        """
        query = (
            "insert into group_constraints (optimization_scenario_id,group_id,period,constraint_type,value) "
            "values (:optimization_scenario_id, :group_id, :period, :constraint_type, :budget_value)"
        )
        argument_list = {
            "optimization_scenario_id": request["optimization_scenario_id"],
            "group_id": int(request["group_id"]),
            "period": request["period"],
            "constraint_type": request["constraint_type"],
            "budget_value": float(request["budget_value"]),
        }
        return self.conn.processqueryinsert(query, argument_list)

    def remove_group_constraint(self, request):
        """
        Parameters
        ----------
        request

        Returns
        -------
        """
        query = "delete from group_constraints where Id = :id"
        argument_list = [{"id": request["Id"]}]
        # print(query,argument_list)
        return self.conn.processqueryinsert(query, argument_list)

    def fetch_optimization_scenario_details(self, request):
        """

        Parameters
        ----------
        request

        Returns
        -------

        """
        query = """
        select
            optimization_type_id,
            outcome_maximize,
            base_scenario_id,
            base_budget,
            incremental_budget,
            total_budget,
            period_year,
            period_start,
            period_end
        from optimization_scenario
        where id = :id
        """
        argument_list = [{"id": int(request["scenario_id"])}]
        return self.conn.processquery(query, argument_list)

    def fetch_base_scenario_ossd(self, optimization_scenario_id, period_type="quarter"):
        """

        Parameters
        ----------
        optimization_scenario_id

        Returns
        -------

        """
        query = """
        select vnm.variable_name as Variable_Name,
            vnm.variable_category as Variable_Category,
            vnm.variable_description as Variable_Description,
            osd.{period_type} as Period,
            CAST(SUM(osd.spend) as float) as spend_value
        from optimization_scenario as os
        join optimization_spend_scenario_data as osd on os.base_scenario_id = osd.scenario_id
        join variable_node_mapping as vnm on osd.variable_id = vnm.variable_id
        where
            os.id = :optimization_scenario_id
        GROUP BY 1,2,3,4
            --vnm.variable_name, vnm.variable_category,vnm.variable_description,osd.{period_type}
        """.format(
            period_type=period_type
        )
        argument_list = [{"optimization_scenario_id": optimization_scenario_id}]
        return self.conn.processquery(query, argument_list)

    def fetch_base_scenario(self, optimization_scenario_id, period_type="quarter"):
        """

        Parameters
        ----------
        optimization_scenario_id

        Returns
        -------

        """
        query = """
        select vnm.variable_name as Variable_Name,
            vnm.variable_category as Variable_Category,
            vnm.variable_description as Variable_Description,
            isb.period as Period,
            isb.base_spend as spend_value
        from optimization_scenario as os
        join individual_spend_bounds as isb on os.id = isb.optimization_scenario_id
        join variable_node_mapping as vnm on isb.variable_id = vnm.variable_id
        where
            os.id = :optimization_scenario_id
        """.format(
            period_type=period_type
        )
        argument_list = [{"optimization_scenario_id": optimization_scenario_id}]
        return self.conn.processquery(query, argument_list)

    def fetch_main_input(self, optimization_scenario_id):
        """

        Parameters
        ----------
        optimization_scenario_id

        Returns
        -------

        """
        query = """
        select om.objective_code as objective_to_max,
            os.period_start, os.period_end,
            os.base_budget as budget_base,
            os.period_type,
            os.period_year,
            os.incremental_budget as budget_incremental,
            os.total_budget as budget_total,
            os.period_type as period_type
        from optimization_scenario as os
        join optimization_type as ot on os.optimization_type_id = ot.id
		join objective_mapping as om on os.outcome_maximize = om.objective_name
        where os.id = :optimization_scenario_id
        """
        argument_list = [{"optimization_scenario_id": optimization_scenario_id}]
        return self.conn.processquery(query, argument_list)

    def fetch_var_group(self):
        """

        Returns
        -------

        """
        query = (
            "select vnm.variable_name, tg.name as group_name from touchpoint_group_variable_mapping as gvm "
            "join variable_node_mapping as vnm on gvm.variable_id = vnm.variable_id "
            "join touchpoint_groups as tg on gvm.group_id = tg.id;"
        )
        return self.conn.processquery(query)

    def fetch_spend_bounds(self, optimization_scenario_id, period_type):
        """

        Parameters
        ----------
        optimization_scenario_id

        Returns
        -------

        """
        query = """
        select vnm.variable_name as Variable_Name,
            vnm.variable_category as Variable_Category,
            vnm.variable_description as Variable_Description,
            isb.lock as Lock,
            isb.period as Period,
            CAST(isb.lowerbound as float) as Lower_Bound,
            CAST(isb.upperbound as float) as Upper_Bound,
            CAST(SUM(isb.base_spend) as float) as Base_Scenario
        from individual_spend_bounds as isb
        join variable_node_mapping as vnm on isb.variable_id = vnm.variable_id
        join optimization_scenario as os on isb.optimization_scenario_id = os.id
        where isb.optimization_scenario_id= :optimization_scenario_id
            and isb.variable_id = vnm.variable_id
        group by 1,2,3,4,5,6,7
        """.format(
            period_type=period_type
        )
        argument_list = [{"optimization_scenario_id": optimization_scenario_id}]
        return self.conn.processquery(query, argument_list)

    def fetch_group_constraints(self, optimization_scenario_id):
        """

        Parameters
        ----------
        optimization_scenario_id

        Returns
        -------

        """
        query = "select tg.name as variable_group, gp.period as period, gp.constraint_type as \
                constraint_type, gp.value as value from group_constraints as gp \
                join touchpoint_groups as tg on gp.group_id = tg.id \
                where gp.optimization_scenario_id = :optimization_scenario_id;"
        argument_list = [{"optimization_scenario_id": optimization_scenario_id}]
        return self.conn.processquery(query, argument_list)

    def fetch_outcome_maximum_list(self):
        """

        Returns
        -------

        """
        query = "select objective_name as name from objective_mapping "
        return self.conn.processquery(query)

    def delete_existing_individual_spend_bounds(self, scenario_id):
        """

        Parameters
        ----------
        scenario_id

        Returns
        -------

        """
        query = "delete from individual_spend_bounds where optimization_scenario_id = :scenario_id"
        argument_list = [{"scenario_id": scenario_id}]
        return self.conn.processqueryinsert(query, argument_list)

    def fetch_optimization_scenario_outcomes(self, optimization_id):
        query = """
        select 'Base' as name,o.Outcome,o.Segment,CAST(o.BaseAttribution as float) as BaseAttribution,CAST(o.MarketingAttribution as float) as MarketingAttribution,CAST(o.BaseAttribution + o.MarketingAttribution as float) as Total
        from optimization_scenario s
        inner join optimization_scenario_outcome o on o.scenarioid = s.base_scenario_id
        inner join models m on m.id = o.model_id and m.active = 1
        inner join scenarios sc on sc.id = s.base_scenario_id 
        where s.id = :optimization_id
        union
        select 'Optimized' as name,o.Outcome,o.Segment,CAST(o.BaseAttribution as float) as BaseAttribution,CAST(o.MarketingAttribution as float) as MarketingAttribution,CAST(o.BaseAttribution + o.MarketingAttribution as float) as Total  from optimization_scenario s
        inner join optimization_scenario_outcome o on o.scenarioid = s.optimized_scenario_id
        inner join models m on m.id = o.model_id and m.active = 1
        inner join scenarios sc on sc.id = s.optimized_scenario_id 
        where s.id = :optimization_id
        """
        argument_list = [{"optimization_id": optimization_id}]
        return self.conn.processquery(query, argument_list)

    def get_media_hierarchy(self):
        query = (
            "SELECT node_id,node_name, parent_node_id, node_display_name, node_description as node_ref_name, node_seq,leaf_nodes "
            "FROM select_touchpoints mh "
        )
        return self.conn.processquery(query)

    def update_individual_spend_bounds(self, data):
        #        print(data)
        query = """
        update individual_spend_bounds
        set
            lock = '{lock}',
            lowerbound = {lowerbound},
            upperbound = {upperbound},
            base_spend = {basespend}
        where
            optimization_scenario_id = {os_id}
            and variable_id = {var_id}
            and period = {period}
            and period_type = '{period_type}'
        """.format(
            lock=data["lock"],
            lowerbound=data["Lower Bound Eff"],
            upperbound=data["Upper Bound Eff"],
            os_id=data["optimization_scenario_id"],
            var_id=data["variable_id"],
            period=data["period"],
            period_type=data["period_type"],
            basespend=data["spend"],
        )
        #        print(query)
        return self.conn.processqueryinsert(query)
    def get_individual_spend_bounds_value(self, data):
        #        print(data)
        query = """
        select lowerbound, upperbound, base_spend from individual_spend_bounds
        where
            optimization_scenario_id = {os_id}
            and variable_id = {var_id}
            and period = {period}
            and period_type = '{period_type}'
        """.format(
            os_id=data["optimization_scenario_id"],
            var_id=data["variable_id"],
            period=data["period"],
            period_type=data["period_type"],
        )
        #        print(query)
        return self.conn.processquery(query)

    def update_individual_spend_lock_unlock_all(self, data):
        if data["lockall"]:
            query = "update individual_spend_bounds set lock = :lock, lowerbound = base_spend, upperbound = base_spend where optimization_scenario_id = :optimization_scenario_id"
        else:
            query = "update individual_spend_bounds set lock = :lock where optimization_scenario_id = :optimization_scenario_id"
        argument_list = {
            "lock": data["lockall"],
            "optimization_scenario_id": data["optimization_scenario_id"],
        }
        return self.conn.processqueryinsert(query, argument_list)


    def get_optimization_base_spend_outcome(self, optimization_scenario_id):
        query = """
            select oso.Outcome,
                oso.Segment,
                CAST(oso.BaseAttribution as float) as BaseAttribution,
                CAST(oso.MarketingAttribution as float) as MarketingAttribution,
                CAST(oso.ExternalAttribution as float) as ExternalAttribution
            from optimization_scenario_outcome as oso
            join optimization_scenario as os on os.base_scenario_id = oso.ScenarioId
            where os.id =  :optimization_scenario_id
        """

        argument_list = [{"optimization_scenario_id": optimization_scenario_id}]
        return self.conn.processquery(query, argument_list)

    def fetch_spend_plan_id(self, optimization_scenario_id):
        query = "select base_scenario_id from optimization_scenario where optimization_scenario.id = :optimization_scenario_id"
        argument_list = [{"optimization_scenario_id": optimization_scenario_id}]
        return self.conn.processquery(query, argument_list)

    def delete_optimization_spend_scenario_data(self, scenario_id):
        query = "delete from optimization_spend_scenario_data where scenario_id=:scenario_id"
        argument_list = [{"scenario_id": scenario_id}]
        return self.conn.processqueryinsert(query, argument_list)

    def fetch_spend_by_id(self, spend_id, period_type=None):
        if period_type is not None:
            query = """
            select vnm.variable_name as 'Variable Name',
                vnm.variable_description as 'Variable Description',
                ossd.{period_type} as 'period_name',
                CAST(SUM(ossd.spend) as float) as 'spend_value'
            from optimization_spend_scenario_data as ossd
            join variable_node_mapping as vnm on ossd.variable_id = vnm.variable_id
            where ossd.scenario_id = :spend_id
            GROUP BY vnm.variable_name,vnm.variable_description,ossd.{period_type}
            """.format(
                period_type=period_type
            )
        else:
            granularities = ["month", "quarter"]
            query = f"""
            select vnm.variable_name as 'Variable Name',
                vnm.variable_description as 'Variable Description',
                {",".join(map(lambda val: 'ossd.'+val, granularities))},
                CAST(SUM(ossd.spend) as float) as 'spend_value'
            from optimization_spend_scenario_data as ossd
            join variable_node_mapping as vnm on ossd.variable_id = vnm.variable_id
            where ossd.scenario_id = :spend_id
            GROUP BY vnm.variable_name,vnm.variable_description,{",".join(map(lambda val: 'ossd.'+val, granularities))}
            """
        argument_list = [{"spend_id": spend_id}]
        return self.conn.processquery(query, argument_list)

    def get_spend_from_spend_scenario_details(
        self, spend_scenario_details_id, period_type
    ):
        query = f"""
        select ssd.period_name as period_name,
            CAST(ssd.spend_value as float) as spend_value,
            vnm.node_id,
            vnm.variable_name as node_name,
            vnm.variable_id
        from spend_scenario_details as ssd
        INNER JOIN variable_node_mapping as vnm on ssd.node_id = vnm.node_id
        where
            ssd.period_type = :period_type
            and ssd.scenario_id = :spend_scenario_details_id
        """
        argument_list = {
            "spend_scenario_details_id": int(spend_scenario_details_id),
            "period_type": period_type,
        }
        return self.conn.processquery(query, argument_list)

    def fetch_spend_from_spend_scenario_details(
        self, spend_scenario_details_id, period_type="quarterly"
    ):
        query = """
            select ssd.period_name as period,
                CAST(ssd.spend_value as float) as spend,
                vnm.variable_id
            from spend_scenario_details as ssd
            INNER JOIN variable_node_mapping as vnm on ssd.node_id = vnm.node_id
            where 
                ssd.period_type =:period_type
                and ssd.scenario_id = :spend_scenario_details_id
            """
        argument_list = {
            "spend_scenario_details_id": int(spend_scenario_details_id),
            "period_type": period_type,
        }
        return self.conn.processquery(query, argument_list)

    def get_optimization_type(self, scenario_id):
        """

        Parameters
        ----------
        scenario_id

        Returns
        List with optimization type id

        """
        query = "select optimization_type_id from optimization_scenario where id = :scenario_id"
        argument_list = {"scenario_id": scenario_id}
        return self.conn.processquery(query, argument_list)

    def get_variable_id(self, group_id):
        group_id = int(group_id)
        query = """
            select variable_id from touchpoint_group_variable_mapping where group_id = :group_id
            """
        arguments_list = {"group_id": group_id}
        return self.conn.processquery(query, arguments_list)

    def get_base_spend_for_group_constraint(
        self,
        variable_id_list,
        scenario_id,
        grp_period,
        period_type="quarter",
        period_start=None,
        period_end=None,
    ):
        if period_start is None:
            period_start = 1
        end_mapping = {"quarter": 4, "month": 12}
        if period_end is None:
            period_end = end_mapping.get(period_type)
        placeholders = ",".join(
            ":var{}".format(i) for i in range(len(variable_id_list))
        )
        if grp_period:
            period_start = grp_period
            period_end = grp_period
        query = """
            SELECT CAST(SUM(spend) AS float) AS base_spend
            FROM optimization_spend_scenario_data
            WHERE scenario_id = :scenario_id
                AND {period_type} >= :period_start
                AND {period_type} <= :period_end
                AND variable_id IN ({placeholders})
        """.format(
            period_type=period_type, placeholders=placeholders
        )

        argument_list = {
            "scenario_id": scenario_id,
            "period_start": period_start,
            "period_end": period_end,
        }
        for i, variable_id in enumerate(variable_id_list):
            argument_list["var{}".format(i)] = variable_id

        return self.conn.processquery(query, argument_list)
