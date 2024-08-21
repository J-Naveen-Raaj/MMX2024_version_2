class MaintenanceDAO(object):

    def __init__(self, conn):
        self.conn = conn

    def get_maintenance_scenario_list(self):
        """
        Returns
        -------
        """
        query = """select os.base_budget,os.base_scenario_id,os.created_on,os.username,
    os.id,os.incremental_budget,os.name as scenario_name,os.optimization_type_id,os.optimized_scenario_id,os.outcome_maximize,
    os.output_file,os.period_end,os.period_start,os.period_type,os.period_year,
    os.status,os.total_budget,s.name as name from optimization_scenario os join scenarios s on s.id = os.base_scenario_id"""
        return self.conn.processquery(query)
    
    def get_maintenance_planner_list(self):
        """
        Returns
        list of scenarios which are created in planner
        """
        query = "select sc.id, sc.name, sc.scenario_type as category,sc.username,sc.created_on,ss.year,ss.spend_value as base_budget, ss.period_type from scenarios sc join spend_scenario ss on sc.name = ss.scenario_name where sc.scenario_type !='Optimized' and sc.active=1"
        return self.conn.processquery(query)

    def get_scenario_name(self, scenario_name,scenario_type):
        """
        Parameters
        ----------
        scenario_name

        Returns
        -------
        """
        query = "select id from scenarios where name = :scenario_name and scenario_type = :scenario_type"
        arguments = {'scenario_name':scenario_name,'scenario_type':scenario_type}
        return self.conn.processquery(query, arguments)

    
    def fetch_individual_basespends(self, optimization_scenario_id):
        """

        Parameters
        ----------
        optimization_scenario_id

        Returns
        details from indivudal_spend_bounds table
        """
        query = """
        select isb.optimization_scenario_id as scenario_id,os.optimization_type_id as scenario_type,
            os.outcome_maximize,os.base_budget,os.total_budget,
            variable_name,
            variable_description,
            isb.period_type,isb.period,lowerbound as "LowerBound($)",upperbound as "UpperBound($)",base_spend as base_spend
        from individual_spend_bounds isb
        inner join variable_node_mapping v on v.variable_id = isb.variable_id
        inner join optimization_scenario os on os.id = isb.optimization_scenario_id
        where isb.optimization_scenario_id = :optimization_scenario_id
        GROUP BY isb.optimization_scenario_id,os.optimization_type_id,os.outcome_maximize,os.base_budget, os.total_budget,
        variable_name, variable_description,isb.period_type,isb.period,isb.lowerbound, isb.upperbound, isb.base_spend
        order by variable_description asc
        """
        argument_list = [
            {
                "optimization_scenario_id": optimization_scenario_id,
            }
        ]
        return self.conn.processquery(query, argument_list)
    def fetch_scenario_outcome(self,scenario_id):
        """

        Parameters
        ----------
        scenario_id

        Returns
        details spend and value from scenario_outcone
        -------
        """
        query= """SELECT outcome,variable_category as Channel_name,variable_description as Tactic_name,segment, quarter, month,node_name,
            SUM(spend_value) AS optimized_spend,
            SUM(value) AS optimized_value,
            scenario_id FROM scenario_outcome inner join variable_node_mapping v on node_name = v.variable_name WHERE scenario_id = :scenario_id
            GROUP BY
            outcome,
            segment,
            quarter,
            month,
            node_name,v.variable_category,v.variable_description,
            scenario_id;"""
        argument_list = [
            {
                "scenario_id": scenario_id}
        ]
        return self.conn.processquery(query, argument_list)

    def delete_from_optimization_scenario(self,optimization_scenario_id):
        """
        Parameters
        ----------
        optimization_scenario_id
        Returns
        -------
        """
        query = "delete from optimization_scenario where id = :optimization_scenario_id"
        argument_list = [
            {
                "optimization_scenario_id": optimization_scenario_id,
            }
        ]
        return self.conn.processqueryinsert(query, argument_list)
    def delete_from_individual_spend(self,optimization_scenario_id):
        """
        Parameters
        ----------
        optimization_scenario_id
        Returns
        -------
        """
        query = "delete from individual_spend_bounds where optimization_scenario_id = :scenario_id"
        argument_list = [
            {
                "scenario_id": optimization_scenario_id,
            }
        ]
        return self.conn.processqueryinsert(query, argument_list)
    def get_scenario_id(self,scenario_name):
        """
        Parameters
        ----------
        scenario_name
        Returns
        id
        -------
        """
        query = "select scenario_id from spend_scenario where scenario_name = :scenario_name"
        argument_list = [
            {
                "scenario_name": scenario_name,
            }
        ]
        return self.conn.processquery(query, argument_list)
    def delete_from_scenario_table(self, scenario_id, table_name):
        """
        Parameters
        ----------
        scenario_id: int
            The scenario ID to be deleted.
        table_name: str
            The name of the table from which to delete the record.
        Returns
        -------
        """
        query = f"DELETE FROM {table_name} WHERE scenario_id = :scenario_id"
        argument_list = [{"scenario_id": scenario_id}]
        return self.conn.processqueryinsert(query, argument_list)
    
    def delete_from_optimization_table(self, scenario_id, table_name, table_column):
        """
        Parameters
        ----------
        scenario_id: int
            The scenario ID to be deleted.
        table_name: str
            The name of the table from which to delete the record.
        Returns
        -------
        """
        query = f"DELETE FROM {table_name} WHERE {table_column} = :scenario_id"
        argument_list = [{"scenario_id": scenario_id}]
        return self.conn.processqueryinsert(query, argument_list)
