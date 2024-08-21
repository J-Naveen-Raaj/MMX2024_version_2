# -*- coding: utf-8 -*-
from pymoo.algorithms.soo.nonconvex.de import DE
from pymoo.core.problem import ElementwiseProblem
from pymoo.operators.sampling.lhs import LHS
from pymoo.optimize import minimize
from pymoo.termination.default import DefaultSingleObjectiveTermination

from app_server.database_handler import DatabaseHandler
from app_server.MMOptim.genetic_alo_utils import (
    convert_spends_to_impression_clicks,
    get_number_of_weeks,
    model_results,
    sum_over_solution_idvs,
    transform,
)
from app_server.scenario_dao import ScenarioDAO

db_conn = DatabaseHandler().get_database_conn()
scenario_dao = ScenarioDAO(db_conn)


import numpy as np
import pandas as pd


class Problem(ElementwiseProblem):
    budget = None
    coefficient_df = None
    mean_scaling_df = None
    dv = None
    idvs = None
    conversion_ratio_df = None
    s_curve_df_outcome1 = None
    s_curve_df_SU = None
    group_constraints = None
    def __init__(
        self,
        xl,
        xu,
        budget,
        mean_scaling_file,
        conversion_ratio_file,
        coefficient_file,
        s_curve_transformation_file,
        group_constraints,
        idvs,
        dv,
    ):
        self.mean_scaling_df = mean_scaling_file
        self.budget = budget
        self.convertion_ratio_df = conversion_ratio_file
        self.s_curve_df = s_curve_transformation_file
        self.coefficient_df = coefficient_file
        self.convertion_ratio_df = self.convertion_ratio_df[
            self.convertion_ratio_df["X_YEAR"] == 2023
        ]
        self.idvs = idvs
        self.dv = dv
        self.group_constraints = group_constraints

        total_n_ieq_constr = 1 + len(group_constraints)
        super().__init__(
            n_var=len(xl), n_obj=1, xl=xl, xu=xu, n_ieq_constr=total_n_ieq_constr
        )

    def _evaluate(self, x, out, *args, **kwargs):
        data_df = pd.DataFrame([x])
        data_df.columns = self.idvs
        converted_df = convert_spends_to_impression_clicks(
            data_df.copy(), self.convertion_ratio_df
        )
        transformed_df = transform(
            self.s_curve_df, converted_df, idvs=list(converted_df.columns)
        )

        preds = model_results(
            mean_scaling_df=self.mean_scaling_df,
            data_df=transformed_df,
            coefficient_df=self.coefficient_df,
            dv=self.dv,
        )

        out["F"] = [-np.exp(preds[0])]

        ineq_cons = []
        budget_constraint = sum(x) - self.budget
        ineq_cons.append(budget_constraint)

        for constraint in self.group_constraints.items():
            sum_of_cons_var = sum_over_solution_idvs(data_df, constraint[1]["var_list"])
            if constraint[0][2] == "Cap":
                ineq_cons.append(sum_of_cons_var - constraint[1]["value"])
            if constraint[0][2] == "Min":
                ineq_cons.append(-sum_of_cons_var + constraint[1]["value"])

        # print("*****")
        # print(data_df[constraint[1]['var_list']])
        # print(constraint[1]['var_list'])
        # print(sum_of_cons_var)
        # print(constraint[1]['value'])      
        out["G"] = ineq_cons


def Differential_Evolution(
    budget,
    lower_bounds,
    upper_bounds,
    dv,
    period_year,
    period_type,
    split_budget_proportion,
    group_constraints,
):
    termination = DefaultSingleObjectiveTermination(n_max_gen=40)

    algorithm = DE(
        pop_size=40,
        n_offsprings=10,
        sampling=LHS(),
        variant="DE/rand/1/bin",
        CR=0.7,
        dither="vector",
        jitter=False,
    )

    solution = upper_bounds.copy()
    print(budget)
    print(lower_bounds)
    print(upper_bounds)
    split = -1
    convergences = []
    for column in solution.columns:
        split = split + 1
        lower_bounds[column] = lower_bounds[column].astype(int)
        upper_bounds[column] = upper_bounds[column].apply(np.ceil).astype(int)

        lower = list(lower_bounds[column].values)
        upper = list(upper_bounds[column].values)

        if lower == upper:
            continue

        if dv == "outcome1":
            transformation_file = pd.DataFrame.from_records(
                scenario_dao.get_ad_stocks_what_if_FTB()
            )
        else:
            transformation_file = pd.DataFrame.from_records(
                scenario_dao.get_ad_stocks_what_if_SU()
            )

        number_of_weeks = get_number_of_weeks(
            period_type=period_type, period_year=period_year, period=column
        )

        lower = [x / number_of_weeks for x in lower]
        upper = [x / number_of_weeks for x in upper]

        budget_optimize = split_budget_proportion[split] * budget / number_of_weeks
        constraints_subset = {}
        for constraint in group_constraints.items():
            if constraint[0][1] == column:
                constraint[1]["value"] = constraint[1]["value"] / number_of_weeks
                constraints_subset[constraint[0]] = constraint[1]

        problem = Problem(
            idvs=list(solution.index),
            xl=lower,
            xu=upper,
            budget=budget_optimize,
            mean_scaling_file=pd.DataFrame.from_records(scenario_dao.get_min_max()),
            conversion_ratio_file=pd.DataFrame.from_records(
                scenario_dao.get_year_ratio()
            ),
            coefficient_file=pd.DataFrame.from_records(
                scenario_dao.get_coefficients_merged()
            ),
            dv=dv,
            s_curve_transformation_file=transformation_file,
            group_constraints=constraints_subset,
        )

        res = minimize(problem, algorithm, termination, seed=1, verbose=True)
        x_results = res.X

        if x_results is None:
            convergence = False
        else:
            convergence = True
            x_results = [x * number_of_weeks for x in x_results]
            solution[column] = x_results
        convergences.append(convergence)

    x = np.round(solution.values.tolist(), decimals=0)
    print(x)
    print(list(solution.index))
    return x, 0, np.all(convergences)
