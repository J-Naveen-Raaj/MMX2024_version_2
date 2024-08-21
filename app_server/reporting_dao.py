
class ReportingDAO(object):
    def __init__(self, conn):
        self.conn = conn

    def touchpoints(self):
        query = (
            "select  m.node_id, m.node_name, m.node_display_name, m.parent_node_id, m.node_seq,m.leaf_nodes, "
            "m.level from select_touchpoints m order by m.node_seq;"
        )
        return self.conn.processquery(query)

    def get_media_hierarchy_old_download_data(self):
        query = (
            "select  m.node_seq, m.node_id, m.level, m.node_description from select_touchpoints m "
            "order by m.node_seq;"
        )
        return self.conn.processquery(query)

    def get_scenario_spend_details(
        self, scenario_id_curr, scenario_id_reff, period_type
    ):
        query = (
            "select r.node_name, r.geo, pm.period_name_short || '_' || {scenario_id_curr} as {period_type}, r.spend_value from "
            "(select node_name, geo, coalesce(sum(spend_value),0)/2 as spend_value, {period_type} from reporting_allocations_temp "
            "where year={scenario_id_curr} "
            "and month in "
            "(select DISTINCT month from reporting_allocations_temp "
            "where year = {scenario_id_reff}) "
            "GROUP BY node_name, geo, {period_type}) as r "
            "inner join period_master as pm on pm.period_id=r.{period_type} and pm.period_type=:period_type".format(
                period_type=period_type,
                scenario_id_curr=scenario_id_curr,
                scenario_id_reff=scenario_id_reff,
            )
        )
        arguments = [{"period_type": period_type}]
        return self.conn.processquery(query, arguments)

    def get_scenario_spend_details_download(
        self, scenario_id_curr, scenario_id_reff, period_type
    ):
        query = (
            "select r.node_name, r.geo, pm.period_name_short || '_' || {scenario_id_curr} as period_name, r.spend_value as spend_value from "
            "(select node_name, geo, coalesce(sum(spend_value),0)/2 as spend_value, {period_type} "
            "from reporting_allocations_temp where year = {scenario_id_curr} "
            "and month in "
            "(select DISTINCT month from reporting_allocations_temp "
            "where year = {scenario_id_reff}) "
            "GROUP BY node_name, geo, {period_type}) as r "
            "inner join period_master as pm on pm.period_id=r.{period_type} and pm.period_type=:period_type".format(
                period_type=period_type,
                scenario_id_curr=scenario_id_curr,
                scenario_id_reff=scenario_id_reff,
            )
        )
        arguments = [{"period_type": period_type}]
        return self.conn.processquery(query, arguments)

    def get_scenario_name(self, scenario_id):
        query = (
            "select scenario_name from spend_scenario where scenario_id = :scenario_id "
        )
        arguments = [{"scenario_id": scenario_id}]
        return self.conn.processquery(query, arguments)

    def get_reporting_allocations_years(self):
        query = ("SELECT DISTINCT year,scenario_id FROM reporting_allocations_temp;")
        
        return self.conn.processquery(query)
    
    def get_reporting_sc_module(self):
        query = ("SELECT * FROM secondary_modules")
        
        return self.conn.processquery(query)
    
    def get_reporting_allocations(self, year, period_type, quarter, month):
        if period_type == "year":
            query = (
                "select node_name,geo,outcome,sum(value) as value "
                "from reporting_allocations_temp ra "
                "where year = {year} group by node_name,outcome,geo".format(year=year)
            )
        elif period_type == "month":
            query = (
                "SELECT node_name, geo, outcome, COALESCE(SUM(value), 0) AS value "
                "FROM reporting_allocations_temp "
                "WHERE year = {year} AND month = {month} "
                "GROUP BY node_name, outcome, geo".format(year=year, month=month)
            )
        else:
            query = (
                "select node_name,geo,outcome,coalesce(sum(value),0) as value "
                "from reporting_allocations_temp ra "
                "where year = {year} and quarter = {quarter} group by node_name,outcome,geo".format(
                    year=year, quarter=quarter
                )
            )
        # print(query)
        return self.conn.processquery(query)

    # "segment" removed in query
    def get_reporting_allocations_download(self, year, period_type, quarter,month):
        if period_type == "year" or period_type == "month":
            query = (
                "select node_name,geo,outcome,quarter,month,sum(value) as value "
                "from reporting_allocations_temp ra "
                "where year = {year} group by node_name,outcome,quarter,geo,month".format(
                    year=year
                )
            )
        else:
            query = (
                "select node_name,geo,outcome,month,coalesce(sum(value),0) as value "
                "from reporting_allocations_temp ra "
                "where year = {year} and quarter = {quarter} group by node_name,outcome,geo,month".format(
                    year=year, quarter=quarter
                )
            )
        # print(query)
        return self.conn.processquery(query)

    def get_scenario_spend(self, year, period_type, period_name,month):


        if period_name == "" or period_type == "year":
            query = (
                "select node_name, geo, coalesce(sum(spend_value),0)/2 as spend_value from"
                " (select node_name, geo, spend_value from reporting_allocations_temp ra"
                " where year = {year}) as t"
                " GROUP BY node_name,geo".format(year=year)
            )
            
        elif period_type == "month":
            query = (
                "select node_name, geo, coalesce(sum(spend_value),0)/2 as spend_value from"
                " (select node_name, geo, spend_value from reporting_allocations_temp ra"
                " where year = {year}"
                " and month={month}) as t"
                " GROUP BY node_name,geo".format(
                    year=year, month=month
                )
            )
        else:
            query = (
                "select node_name, geo, coalesce(sum(spend_value),0)/2 as spend_value from"
                " (select node_name, geo, spend_value from reporting_allocations_temp ra"
                " where year = {year}"
                " and quarter={period_name}) as t"
                " GROUP BY node_name,geo".format(
                    year=year, period_name=period_name
                )
            )

        return self.conn.processquery(query)

    def get_scenario_spend_download(self, year, period_type, period_name,month):

        if period_name == "" or period_type == "year" or period_type == "month":
            query = (
                "select node_name, geo, quarter, month, coalesce(sum(spend_value),0)/2 as spend_value from"
                " (select node_name, geo, quarter, month, spend_value from reporting_allocations_temp ra"
                " where year = {scenario_id}) as t"
                " GROUP BY node_name,geo,quarter, month".format(scenario_id=year)
            )

        else:
            query = (
                "select node_name, geo, month, coalesce(sum(spend_value),0)/2 as spend_value from"
                " (select node_name, geo, spend_value, month from reporting_allocations_temp ra"
                " where year = {scenario_id}"
                " and quarter={period_name}) as t"
                " GROUP BY node_name,geo,month".format(
                    scenario_id=year, period_name=period_name.replace("Q", "")
                )
            )

        return self.conn.processquery(query)

    def get_scenario_spend_allocations(
        self, scenario_id_curr, scenario_id_reff, outcome, period_type
    ):
        query = (
            "select node_name, geo, {period}, sum(allocation) as allocation "
            "from (select r.node_name, r.geo, r.outcome, pm.period_name_short || '_' || :scenario_id_curr as {period}, r.value as allocation "
            "from reporting_allocations_temp r "
            "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type = :period_type "
            "where year = :scenario_id_curr and r.outcome = :outcome "
            "and month in "
            "(select DISTINCT month from reporting_allocations_temp ra "
            "where year = :scenario_id_reff)) as t "
            "group by node_name, geo, {period}".format(period=period_type)
        )

        arguments = {
            "period_type": period_type,
            "scenario_id_curr": scenario_id_curr,
            "outcome": outcome,
            "scenario_id_reff": scenario_id_reff,
        }

        # print(query,arguments)

        return self.conn.processquery(query, arguments)

    def get_scenario_spend_allocations_temp(
        self, scenario_id_curr, scenario_id_reff, outcome, period_type,quarter1,month,halfyear
    ):
        if period_type == "year":
            query = (
                "select node_name, geo, {period}, sum(allocation) as allocation "
                "from (select r.node_name, r.geo, r.outcome, pm.period_name_short || '_' || :scenario_id_curr as {period}, r.value as allocation "
                "from reporting_allocations_temp r "
                "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type = :period_type "
                "where year = :scenario_id_curr and r.outcome = :outcome "
                "and month in "
                "(select DISTINCT month from reporting_allocations_temp ra "
                "where year = :scenario_id_reff)) as t "
                "group by node_name, geo, {period}".format(period=period_type)
            )

            arguments = {
                "period_type": period_type,
                "scenario_id_curr": scenario_id_curr,
                "outcome": outcome,
                "scenario_id_reff": scenario_id_reff,
            }
        elif period_type == "quarter":
            query = (
                "select node_name, geo, {period}, sum(allocation) as allocation "
                "from (select r.node_name, r.geo, r.outcome, pm.period_name_short || '_' || :scenario_id_curr as {period}, r.value as allocation "
                "from reporting_allocations_temp r "
                "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type = :period_type "
                "where year = :scenario_id_curr and r.outcome = :outcome and r.quarter = {quarter} "
                "and month in "
                "(select DISTINCT month from reporting_allocations_temp ra "
                "where year = :scenario_id_reff)) as t "
                "group by node_name, geo, {period}".format(period=period_type,quarter=quarter1.replace("Q", ""))
            )
            arguments = {
                    "period_type": period_type,
                    "scenario_id_curr": scenario_id_curr,
                    "outcome": outcome,
                    "scenario_id_reff": scenario_id_reff,
                }
        elif period_type == "month":
            query = (
                "select node_name, geo, {period}, sum(allocation) as allocation "
                "from (select r.node_name, r.geo, r.outcome, pm.period_name_short || '_' || :scenario_id_curr as {period}, r.value as allocation "
                "from reporting_allocations_temp r "
                "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type = :period_type "
                "where year = :scenario_id_curr and r.outcome = :outcome and r.month = {month} "
                "and month in "
                "(select DISTINCT month from reporting_allocations_temp ra "
                "where year = :scenario_id_reff)) as t "
                "group by node_name, geo, {period}".format(period=period_type,month=month)
            )
            arguments = {
                    "period_type": period_type,
                    "scenario_id_curr": scenario_id_curr,
                    "outcome": outcome,
                    "scenario_id_reff": scenario_id_reff,
                }
        else:
            query = (
                "select node_name, geo, {period}, sum(allocation) as allocation "
                "from (select r.node_name, r.geo, r.outcome, pm.period_name_short || '_' || :scenario_id_curr as {period}, r.value as allocation "
                "from reporting_allocations_temp r "
                "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type = :period_type "
                "where year = :scenario_id_curr and r.outcome = :outcome and r.halfyear = {halfyear} "
                "and month in "
                "(select DISTINCT month from reporting_allocations_temp ra "
                "where year = :scenario_id_reff)) as t "
                "group by node_name, geo, {period}".format(period=period_type,halfyear=halfyear.replace("H", ""))
            )
            arguments = {
                    "period_type": period_type,
                    "scenario_id_curr": scenario_id_curr,
                    "outcome": outcome,
                    "scenario_id_reff": scenario_id_reff,
                }
        # print(query,arguments)

        return self.conn.processquery(query, arguments)
    def get_scenario_spend_allocations_download(
        self, scenario_id_curr, scenario_id_reff, period_type
    ):

        """
        Perameters:
            scenario_id: interested scenario id (eg. 1,2 etc.)
            period_type: interesed period type. Can take only three values. {year, halfyear, quarter}
        Returns:
            A dataframe containing allocations for specific scenariod and period
            period_type = year, output dataframe size = (183,5)
            period_type = halfyear, output dataframe size = (366,5)
            period_type = quarter, output dataframe size = (732,5)
            No. of columns are fixed for each query
        """

        query = (
            "select outcome,node_name,geo,period_name,sum(allocation) as allocation from "
            "(select r.outcome, r.node_name, r.geo, pm.period_name_short || '_' || {scenario_id_curr} as period_name, r.value as allocation "
            "from reporting_allocations_temp r "
            "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type=:period_type "
            "where year =:scenario_id_curr "
            "and month in "
            "(select DISTINCT month from reporting_allocations_temp ra "
            "where year = {scenario_id_reff})) as t "
            "group by t.node_name, t.geo, t.outcome, t.period_name ".format(
                period=period_type,
                scenario_id_curr=scenario_id_curr,
                scenario_id_reff=scenario_id_reff,
            )
        )
        arguments = [{"period_type": period_type, "scenario_id_curr": scenario_id_curr}]
        # print(query,arguments)
        return self.conn.processquery(query, arguments)

    def get_scenario_list_for_mrc(self):
        query = """SELECT distinct ss.scenario_id,ss.scenario_name
                  FROM reporting_marginal_curves_latest mrc
                  inner join spend_scenario ss on ss.scenario_id = mrc.scenario_id"""
        # FROM [dbo].[reporting_marginal_curves_latest] mrc
        return self.conn.processquery(query)

    def get_marginal_return_curves_data(self, nodes, scenario_id):
        nodes = [int(i) for i in nodes]
        if len(nodes) != 1:
            query = (
                "SELECT rm.node_id, ROUND(CAST(spend_change_pct AS numeric), 0) AS spend_change, mh.node_description AS node_display_name, rm.outcome, "
                "ROUND(CAST(value_change AS numeric), 0) AS value, ROUND(CAST(value AS numeric), 0) AS value_change "
                "FROM reporting_marginal_curves_latest AS rm "
                "INNER JOIN select_touchpoints AS mh ON mh.node_id = rm.node_id "
                "WHERE rm.segment='Rakuten' AND rm.node_id IN {seq}".format(seq=tuple(nodes))

            )
        else:
            query = (
                "SELECT rm.node_id, ROUND(CAST(spend_change_pct AS numeric), 0) AS spend_change, mh.node_description AS node_display_name, rm.outcome, "
                "ROUND(CAST(value_change AS numeric), 0) AS value, ROUND(CAST(value AS numeric), 0) AS value_change "
                "FROM reporting_marginal_curves_latest AS rm "
                "INNER JOIN select_touchpoints AS mh ON mh.node_id = rm.node_id "
                "WHERE rm.segment = 'Rakuten' AND rm.node_id = {seq}".format(seq=nodes[0])
            )

        arguments = {"scenario_id": scenario_id}

        return self.conn.processquery(query, arguments)

    def get_marginal_return_curves_base_spend_data(self, nodes, scenario_id):
        if len(nodes) != 1:
            query = (
                "SELECT ROUND(CAST(spends AS numeric), 0) AS base_spend, mh.node_description AS node_display_name "
                "FROM reporting_marginal_curves_latest AS rm "
                "INNER JOIN select_touchpoints AS mh ON mh.node_id = rm.node_id "
                "WHERE rm.segment = 'Rakuten' AND rm.spend_change = 0 AND rm.outcome = 'outcome1' AND rm.node_id IN {seq}".format(seq=tuple(nodes))

            )
        else:
            query = (
                "SELECT ROUND(CAST(spends AS numeric), 0) AS base_spend, mh.node_description AS node_display_name "
                "FROM reporting_marginal_curves_latest AS rm "
                "INNER JOIN select_touchpoints AS mh ON mh.node_id = rm.node_id "
                "WHERE rm.segment = 'Rakuten' AND rm.spend_change = 0 AND rm.outcome = 'outcome1' AND rm.node_id = {seq}".format(seq=nodes[0])

            )
        # Add below where condition if scenario id is requried
        # "where rm.scenario_id = :scenario_id and rm.segment='Rakuten' and rm.spend_change = 0 "

        

        arguments = {"scenario_id": scenario_id}

        return self.conn.processquery(query, arguments)

    def get_marginal_return_curves_download_data(self, nodes, scenario_id):
        # scenario_id = int(scenario_id)
        query = (
            "select rm.node_id, mh.node_description as node_display_name,  ROUND(CAST(spend_change AS numeric), 0)  as spend_change, rm.outcome,"
            "ROUND(CAST(value AS numeric), 0) as Value,ROUND(CAST(value_change AS numeric), 0) as Value_Change, spend_change_pct "
            "from reporting_marginal_curves_latest as rm "
            "inner join select_touchpoints as mh on mh.node_id = rm.node_id "
            "where rm.segment='Rakuten' and rm.node_id in {seq} ".format(
                seq=tuple(nodes)
            )
        )

        # arguments = {"scenario_id": scenario_id}

        return self.conn.processquery(query)

    def get_reporting_groups_orders(self, group):
        column = self.get_reporting_groups(group)
        query = (
            "select distinct t.group_header,t.group_name,t.group_order as order1,r.group_name as category,r.group_order as order2 "
            "from reporting_group_orders r "
            "inner join "
            "(select group_header,group_name,group_order,order_by,{column} as group_order_name from reporting_group_orders r "
            "inner join reporting_groups g on {group} = r.group_name "
            "where group_header = '{group}' "
            ") as t "
            "on t.group_order_name = r.group_name and t.order_by = r.group_header "
            "order by order2, order1".format(column=column[0]["order_by"], group=group)
        )
        # print(query)
        return self.conn.processquery(query)

    def get_reporting_groups_by_nodes(self):
        query = "select * from reporting_groups"

        return self.conn.processquery(query)

    def get_period_master_data(self, period_type):
        query = "select period_id, period_name_short as period_name from period_master where period_type = :period_type"
        arguments = [{"period_type": period_type}]

        return self.conn.processquery(query, arguments)

    def get_total_scenario_spend_details(
        self, scenario_id_curr, scenario_id_ref, period_type, quarter
    ):
        if period_type == "year":
            query = (
                "select coalesce(sum(spend_value),0) as spend from"
                " (select node_name, month, COALESCE(sum(NULLIF(spend_value, 'NaN'))/2,0) as spend_value from reporting_allocations_temp"
                " where year = :scenario_id_curr GROUP BY node_name, month "
                " HAVING month in ("
                " select DISTINCT month from reporting_allocations_temp"
                " where year = {scenario_id_ref})) as t".format(
                    scenario_id_ref=scenario_id_ref
                )
            )

        elif period_type == "halfyear":
            query = (
                "select coalesce(sum(spend_value),0) as spend from"
                " (select node_name,halfyear, month, COALESCE(sum(NULLIF(spend_value, 'NaN'))/2,0) as spend_value from reporting_allocations_temp"
                " where scenario_id = :scenario_id_curr GROUP BY node_name,halfyear, month"
                " HAVING halfyear={quarter}) as t ".format(
                    quarter=quarter.replace("H", "")
                )
            )
        elif period_type == "month":
            query = (
                "select coalesce(sum(spend_value),0) as spend from"
                " (select node_name, month, COALESCE(sum(NULLIF(spend_value, 'NaN'))/2,0) as spend_value from reporting_allocations_temp"
                " where year = :scenario_id_curr GROUP BY node_name, month"
                " HAVING month={quarter}) as t ".format(quarter=quarter)
                )

        else:
            query = (
                "select coalesce(sum(spend_value),0) as spend from"
                " (select node_name,quarter, month, COALESCE(sum(NULLIF(spend_value, 'NaN'))/2,0) as spend_value from reporting_allocations_temp"
                " where year = :scenario_id_curr GROUP BY node_name,quarter, month"
                " HAVING quarter={quarter}) as t ".format(
                    quarter=quarter.replace("Q", "")
                )
            )

        arguments = [{"scenario_id_curr": scenario_id_curr}]
        return self.conn.processquery(query, arguments)

    def get_scenario_spend_allocations_total(
        self,
        scenario_id_curr,
        scenario_id_ref,
        outcome,
        include_control,
        period_type,
        quarter,
    ):

        if include_control:
            n_query = "select node_name from media_hierarchy where node_name <> ''"

        else:
            n_query = "select node_name from media_hierarchy where node_name <> '' and node_id > 2000"
        if period_type == "year":
            query = (
                "select sum(value) as outcome"
                " from reporting_allocations_temp"
                " where outcome = :outcome"
                " and year = :scenario_id_curr"
                " and month in"
                " (select DISTINCT month"
                " from reporting_allocations_temp"
                " where year = {scenario_id_ref})".format(
                    scenario_id_ref=scenario_id_ref
                )
            )

        elif period_type == "halfyear":
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from reporting_allocations_temp"
                " where outcome = :outcome  and scenario_id = :scenario_id_curr"
                " and halfyear={quarter} ".format(quarter=quarter.replace("H", ""))
            )
        elif period_type == "month":
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from reporting_allocations_temp"
                " where outcome = :outcome  and year = :scenario_id_curr"
                " and month={quarter} ".format(quarter=quarter)
            )
        else:
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from reporting_allocations_temp"
                " where outcome = :outcome  and year = :scenario_id_curr"
                " and quarter={quarter} ".format(quarter=quarter.replace("Q", ""))
            )

        arguments = [{"outcome": outcome, "scenario_id_curr": scenario_id_curr}]
        return self.conn.processquery(query, arguments)
    
    def get_scenario_spend_allocations_total_cftbs(
        self,
        scenario_id_curr,
        scenario_id_ref,
        outcome,
        include_control,
        period_type,
        quarter,
    ):

        if include_control:
            n_query = "select node_name from media_hierarchy where node_name <> ''"

        else:
            n_query = "select node_name from media_hierarchy where node_name <> '' and node_id > 2000"
        if period_type == "year":
            query = (
                "select sum(value) as outcome"
                " from reporting_allocations_temp"
                " where outcome = :outcome"
                " and year = :scenario_id_curr and node_name LIKE 'M%'"
                " and month in"
                " (select DISTINCT month"
                " from reporting_allocations_temp"
                " where year = {scenario_id_ref})".format(
                    scenario_id_ref=scenario_id_ref
                )
            )

        elif period_type == "halfyear":
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from reporting_allocations_temp"
                " where outcome = :outcome  and scenario_id = :scenario_id_curr and node_name LIKE 'M%'"
                " and halfyear={quarter} ".format(quarter=quarter.replace("H", ""))
            )
        elif period_type == "month":
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from reporting_allocations_temp"
                " where outcome = :outcome  and year = :scenario_id_curr and node_name LIKE 'M%'"
                " and month={quarter} ".format(quarter=quarter)
            )
        else:
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from reporting_allocations_temp"
                " where outcome = :outcome  and year = :scenario_id_curr and node_name LIKE 'M%'"
                " and quarter={quarter} ".format(quarter=quarter.replace("Q", ""))
            )

        arguments = [{"outcome": outcome, "scenario_id_curr": scenario_id_curr}]
        return self.conn.processquery(query, arguments)

    # For reading data from database as per the provided query and arguments
    def fetch_allocation_period(
        self, scenario_id_curr, scenario_id_reff, period_type, specific_period, outcome
    ):

        query = (
            "select r.node_name,pm.period_name_short as {period}, sum(r.value) as allocation from reporting_allocations_temp r "
            "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type=:period_type "
            "where year = :scenario_id_curr and r.outcome = :outcome "
            "and month in "
            "(select DISTINCT month from reporting_allocations_temp where year = {scenario_id_reff}) "
            "and pm.period_id = :specific_period group by r.node_name, r.outcome, pm.period_name_short ORDER BY r.node_name".format(
                period=period_type,
                scenario_id_reff=scenario_id_reff,
                outcome=outcome,
                specific_period=specific_period,
            )
        )
        arguments = [
            {
                "period_type": period_type,
                "scenario_id_curr": scenario_id_curr,
                "outcome": outcome,
                "specific_period": specific_period,
            }
        ]
        return self.conn.processquery(query, arguments)

    # For reading data from database as per the provided query and arguments
    def fetch_spends(self, scenario_id_curr, scenario_id_reff, period_type):
        query = (
            "select r.node_name, pm.period_name_short as period_name, r.spend_value from "
            "(select node_name, coalesce(sum(spend_value),0)/2 as spend_value, {period_type} "
            "from reporting_allocations_temp where year ={scenario_id_curr} "
            "and month in "
            "(select DISTINCT month from reporting_allocations_temp where year = {scenario_id_reff}) "
            " GROUP BY node_name, {period_type}) as r "
            "inner join period_master as pm on pm.period_id=r.{period_type} and pm.period_type=:period_type".format(
                period_type=period_type,
                scenario_id_curr=scenario_id_curr,
                scenario_id_reff=scenario_id_reff,
            )
        )
        arguments = [{"period_type": period_type}]
        return self.conn.processquery(query, arguments)

    def fetch_node_data(self):
        query = (
            "SELECT node_display_name, node_name  from select_touchpoints mh "
        )
        return self.conn.processquery(query)

    def get_reporting_groups(self, group):
        query = "select distinct order_by from reporting_group_orders where group_header = '{group}' ".format(
            group=group
        )

        return self.conn.processquery(query)

    def get_scenario_spend_romi_cpa(self, from_year, to_year, period_type):


        query = (
            "select node_name, geo, year, halfyear, quarter, month, coalesce(sum(spend_value),0)/2 as spend_value from"
            " (select node_name, geo, year, spend_value, halfyear, quarter, month from reporting_allocations_temp ra"
            " where year between :from_scenario_id and :to_scenario_id ) as t"
            " GROUP BY node_name,geo, year, halfyear, quarter, month order by year, node_name, halfyear, quarter, month"
        )

        arguments = {
            "from_scenario_id": from_year,
            "to_scenario_id": to_year,
        }

        return self.conn.processquery(query, arguments)

    def get_allocations_for_cpa_romi(self, from_year, to_year):

        query = """
                select  node_name, geo, year, halfyear, outcome, quarter, month, coalesce(sum(value),0) as value
                from reporting_allocations_temp ra 
                where year between :from_year and :to_year group by node_name, geo, outcome, year, halfyear, quarter, month 
                order by year, halfyear, quarter, node_name, month
                """
        arguments = {"from_year": from_year, "to_year": to_year}

        return self.conn.processquery(query, arguments)

    # def get_scenario_by_period(self, year, quarter, month, period_type):
        if period_type == "quarter":
            query = (
                "select distinct scenario_id from reporting_allocations_temp where"
                " year=%(year)s and quarter=%(quarter)s"
            )
            arguments = {"year": int(year), "quarter": int(quarter)}

        elif period_type == "year":
            query = (
                "select distinct scenario_id from reporting_allocations_temp where"
                " year=%(year)s"
            )
            arguments = {"year": int(year)}
        else:
            query = (
                "select distinct scenario_id from reporting_allocations_temp where"
                " year=%(year)s and month=%(month)s"
            )
            arguments = {"year": int(year), "month": int(month)}
        return self.conn.processquery(query, arguments)