class ScenarioComparisonDAO(object):
    def __init__(self, conn):
        self.conn = conn

    def get_media_hierarchy(self):
        query = (
            "select m.node_id, m.node_name, m.node_display_name, m.parent_node_id, m.node_seq,m.leaf_nodes "
            "from select_touchpoints m "
            "order by m.node_seq;"
        )
        return self.conn.processquery(query)

    def touchpoints(self):
        query = (
            "select  m.node_id, m.node_name, m.node_display_name, m.parent_node_id, m.node_seq,m.leaf_nodes, "
            "m.level from select_touchpoints m order by m.node_seq;"
        )
        return self.conn.processquery(query)

    def fetch_year(self, scenario_id):
        query = "select year from spend_scenario where scenario_id = :scenario_id"
        arguments = [
            {
                "scenario_id": scenario_id,
            }
        ]
        return self.conn.processquery(query, arguments)

    def fetch_allocation_period(
        self, scenario_id_curr, scenario_id_reff, period_type, specific_period, outcome
    ):
        if period_type == "year":
            query = (
                "select r.node_name,pm.period_name_short as {period}, sum(r.value) as allocation from scenario_outcome r "
                "inner join period_master as pm on pm.period_id = :specific_period and pm.period_type=:period_type "
                "where scenario_id = :scenario_id_curr and r.outcome = :outcome "
                "and month in "
                "(select DISTINCT month from scenario_outcome where scenario_id = {scenario_id_reff}) "
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
        else:
            query = (
                "select r.node_name,pm.period_name_short as {period}, sum(r.value) as allocation from scenario_outcome r "
                "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type=:period_type "
                "where scenario_id = :scenario_id_curr and r.outcome = :outcome "
                "and month in "
                "(select DISTINCT month from scenario_outcome where scenario_id = {scenario_id_reff}) "
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

    def fetch_spends(self, scenario_id_curr, scenario_id_reff, period_type):
        query = (
            "select r.node_name, pm.period_name_short as period_name, r.spend_value from "
            "(select node_name, coalesce(sum(spend_value),0)/2 as spend_value, {period_type} "
            "from scenario_outcome where scenario_id={scenario_id_curr} "
            "and month in "
            "(select DISTINCT month from scenario_outcome where scenario_id = {scenario_id_reff}) "
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
        query = "SELECT node_display_name, node_name  from select_touchpoints mh "
        return self.conn.processquery(query)

    def get_media_hierarchy_download_data(self):
        query = (
            "select  m.node_seq, m.node_id, m.level, m.node_description "
            "from select_touchpoints m "
            "order by m.node_seq;"
        )
        return self.conn.processquery(query)

    def get_scenario_spend_details(self, scenario_id, period_type):
        if period_type == "month":
            add_column = ""
        else:
            add_column = "month,"
        query = """
            select r.node_name,
                pm.period_name_short || '_' || {scenario_id} as {period_type},
                CAST(spend_value as float) as spend_value
            from
                (select node_name,
                    sum(spend_value) as spend_value,
                    {period_type}
                from
                    (select DISTINCT {add_column} {period_type},
                        node_name,
                        spend_value
                    from scenario_outcome so
                    where scenario_id={scenario_id}
                    ) as t
                GROUP BY node_name, {period_type}
                ) as r
            inner join period_master as pm on pm.period_id=r.{period_type}
                and pm.period_type=:period_type
            """.format(
            period_type=period_type, scenario_id=scenario_id, add_column=add_column
        )
        arguments = {"period_type": period_type}
        return self.conn.processquery(query, arguments)

    def get_scenario_spend_details_download(
        self, scenario_id_curr, scenario_id_reff, period_type
    ):
        if period_type == "month":
            add_column = ""
        else:
            add_column = "month,"

        query = (
            "select r.node_name, pm.period_name_short as period_name, spend_value from "
            "(select node_name, sum(spend_value) as spend_value, {period_type} from "
            "(select DISTINCT {add_column} {period_type}, node_name, spend_value from scenario_outcome so "
            " where scenario_id={scenario_id_curr}) as t "
            " GROUP BY node_name, {period_type}) as r "
            " inner join period_master as pm on pm.period_id=r.{period_type} and pm.period_type=:period_type ".format(
                period_type=period_type,
                scenario_id_curr=scenario_id_curr,
                scenario_id_reff=scenario_id_reff,
                add_column=add_column,
            )
        )
        arguments = [{"period_type": period_type}]
        return self.conn.processquery(query, arguments)

    def get_scenario_name(self, scenario_id):
        query = (
            "select scenario_name from spend_scenario where scenario_id=:scenario_id "
        )
        arguments = [{"scenario_id": scenario_id}]
        return self.conn.processquery(query, arguments)

    def get_scenario_spend_allocations(self, scenario_id, outcome, period_type):
        query = """
            select node_name,
                {period},
                CAST(sum(allocation) as float) as allocation
            from
                (select r.node_name,
                    r.outcome,
                    pm.period_name_short || '_' || {scenario_id} as {period},
                    r.value as allocation
                from scenario_outcome r
                inner join period_master as pm on pm.period_id = r.{period}
                    and pm.period_type = :period_type
                where scenario_id = :scenario_id
                and r.outcome = :outcome
                ) as t
            group by t.node_name, t.outcome, t.{period}
            order by node_name
            """.format(
            period=period_type, scenario_id=scenario_id
        )

        arguments = [
            {"period_type": period_type, "scenario_id": scenario_id, "outcome": outcome}
        ]
        return self.conn.processquery(query, arguments)

    def get_scenario_spend_allocations_graph(
        self, scenario_id_curr, scenario_id_reff, outcome, period_type
    ):
        query = (
            "select node_name, {period}, sum(allocation) as allocation "
            "from (select r.node_name, r.outcome, pm.period_name_short || '_' || :scenario_id_curr as {period}, r.value as allocation "
            "from scenario_outcome r "
            "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type = :period_type "
            "where scenario_id = :scenario_id_curr and r.outcome = :outcome "
            "and month in "
            "(select DISTINCT month from scenario_outcome ra "
            "where scenario_id = :scenario_id_reff)) as t "
            "group by node_name, {period}".format(period=period_type)
        )

        arguments = {
            "period_type": period_type,
            "scenario_id_curr": scenario_id_curr,
            "outcome": outcome,
            "scenario_id_reff": scenario_id_reff,
        }

        return self.conn.processquery(query, arguments)

    def get_scenario_spend_details_graph(
        self, scenario_id_curr, scenario_id_reff, period_type
    ):
        query = (
            "select r.node_name, pm.period_name_short || '_' || {scenario_id_curr} as {period_type}, r.spend_value from "
            "(select node_name, coalesce(sum(spend_value),0)/2 as spend_value, {period_type} from scenario_outcome "
            "where scenario_id={scenario_id_curr} "
            "and month in "
            "(select DISTINCT month from scenario_outcome "
            "where scenario_id = {scenario_id_reff}) "
            "GROUP BY node_name, {period_type}) as r "
            "inner join period_master as pm on pm.period_id=r.{period_type} and pm.period_type=:period_type".format(
                period_type=period_type,
                scenario_id_curr=scenario_id_curr,
                scenario_id_reff=scenario_id_reff,
            )
        )
        arguments = [{"period_type": period_type}]
        return self.conn.processquery(query, arguments)

    def get_scenario_spend_allocations_download(
        self, scenario_id_curr, scenario_id_reff, period_type
    ):
        """
        Perameters:
            scenario_id: interested scenario id (eg. 1,2 etc.)
            period_type: interesed period type. Can take only three values. {year, halfyear, quarter}
        Returns:
            A dataframe containing allocations for specific scenario and period
            period_type = year, output dataframe size = (183,4)
            period_type = halfyear, output dataframe size = (366,4)
            period_type = quarter, output dataframe size = (732,4)
            No. of columns are fixed for each query
        """

        query = (
            "select r.outcome, r.node_name, pm.period_name_short as period_name, sum(r.value) as allocation from scenario_outcome r "
            "inner join period_master as pm on pm.period_id = r.{period} and pm.period_type=:period_type "
            "and month in "
            "(select DISTINCT month from scenario_outcome so where scenario_id = {scenario_id_reff}) "
            "where scenario_id = :scenario_id_curr group by r.node_name, r.outcome, pm.period_name_short ".format(
                period=period_type, scenario_id_reff=scenario_id_reff
            )
        )
        arguments = {"period_type": period_type, "scenario_id_curr": scenario_id_curr}
        return self.conn.processquery(query, arguments)

    def get_period_master_data(self, period_type):
        query = "select period_id, period_name_short as period_name from period_master where period_type = :period_type"
        arguments = [{"period_type": period_type}]

        return self.conn.processquery(query, arguments)

    def get_total_scenario_spend_details_new(
        self, scenario_id_curr, scenario_id_ref, period_type, quarter
    ):
        if period_type == "year":
            query = (
                "select coalesce(sum(spend_value),0) as spend from"
                " (select DISTINCT month, node_name, spend_value from scenario_outcome so"
                " where scenario_id = :scenario_id_curr and"
                " month in ("
                " select DISTINCT month from scenario_outcome so"
                " where scenario_id = {scenario_id_ref})) as t".format(
                    scenario_id_ref=scenario_id_ref
                )
            )

        elif period_type == "month":
            query = (
                "select coalesce(sum(spend_value),0) as spend from"
                " (select DISTINCT month, node_name, spend_value from scenario_outcome so"
                " where scenario_id = :scenario_id_curr and"
                " month={quarter}) as t ".format(quarter=quarter)
            )

        else:
            query = (
                "select coalesce(sum(spend_value),0) as spend from"
                " (select DISTINCT month, node_name, spend_value from scenario_outcome so"
                " where scenario_id =:scenario_id_curr and"
                " quarter={quarter}) as t ".format(quarter=quarter.replace("Q", ""))
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
            n_query = "select node_name from select_touchpoints where node_name <> ''"

        else:
            n_query = "select node_name from select_touchpoints where node_name <> '' and node_id > 2000"
        if period_type == "year":
            query = (
                "select sum(value) as outcome"
                " from scenario_outcome so"
                " where outcome = :outcome"
                " and scenario_id = :scenario_id_curr"
                " and month in"
                " (select DISTINCT month"
                " from scenario_outcome so"
                " where scenario_id = {scenario_id_ref})".format(
                    scenario_id_ref=scenario_id_ref
                )
            )

        elif period_type == "month":
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from scenario_outcome so"
                " where outcome = :outcome  and scenario_id = :scenario_id_curr"
                " and month={quarter} ".format(quarter=quarter)
            )
        else:
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from scenario_outcome so"
                " where outcome = :outcome  and scenario_id = :scenario_id_curr"
                " and quarter={quarter} ".format(quarter=quarter.replace("Q", ""))
            )

        arguments = [{"outcome": outcome, "scenario_id_curr": scenario_id_curr}]
        return self.conn.processquery(query, arguments)

    ## Added some new function for download_data to work

    # def get_period_master(self):
    #     query = "select * from period_master"
    #     return self.conn.processquery(query)

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
            n_query = "select node_name from select_touchpoints where node_name <> ''"

        else:
            n_query = "select node_name from select_touchpoints where node_name <> '' and node_id > 2000"
        if period_type == "year":
            query = (
                "select sum(value) as outcome"
                " from scenario_outcome so"
                " where outcome = :outcome"
                " and scenario_id = :scenario_id_curr and node_name LIKE 'M%'"
                " and month in"
                " (select DISTINCT month"
                " from scenario_outcome so"
                " where scenario_id = {scenario_id_ref})".format(
                    scenario_id_ref=scenario_id_ref
                )
            )

        elif period_type == "month":
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from scenario_outcome so"
                " where outcome = :outcome  and scenario_id = :scenario_id_curr and node_name LIKE 'M%'"
                " and month ={quarter} ".format(quarter=quarter)
            )
        else:
            query = (
                "select coalesce(sum(value),0) as outcome"
                " from scenario_outcome so"
                " where outcome = :outcome  and scenario_id = :scenario_id_curr and node_name LIKE 'M%'"
                " and quarter={quarter} ".format(quarter=quarter.replace("Q", ""))
            )

        arguments = [{"outcome": outcome, "scenario_id_curr": scenario_id_curr}]
        return self.conn.processquery(query, arguments)

    def get_allocations_for_cpa_romi(self, scenario):
        query = """
                select  node_name,scenario_id, halfyear, outcome, quarter, month, coalesce(sum(value),0) as value
                from scenario_outcome ra 
                where scenario_id={seq} group by node_name, outcome, scenario_id, halfyear, quarter, month 
                order by scenario_id, halfyear, quarter, node_name, month
                """.format(
            seq=scenario
        )

        return self.conn.processquery(query)

    def get_scenario_spend_romi_cpa(self, scenario):
        query = (
            "select node_name, scenario_id, halfyear, quarter, month, coalesce(sum(spend_value),0)/9 as spend_value from"
            " (select node_name, scenario_id, spend_value, halfyear, quarter, month from scenario_outcome ra"
            "  where scenario_id=:scenario ) as t"
            " GROUP BY node_name, scenario_id, halfyear, quarter, month order by scenario_id, node_name, halfyear, quarter, month"
        )

        arguments = {
            "scenario": scenario,
        }

        return self.conn.processquery(query, arguments)
