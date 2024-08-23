from pymoo.algorithms.moo.nsga2 import NSGA2

# from pymoo.core.problem import Problem
from pymoo.core.problem import ElementwiseProblem
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
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
    dvs = ["outcome1", "outcome2"]
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
        idvs,
        group_constraints,
    ):

        self.mean_scaling_df = mean_scaling_file
        self.budget = budget
        self.convertion_ratio_df = conversion_ratio_file
        self.s_curve_df_outcome1 = s_curve_transformation_file[0]
        self.s_curve_df_SU = s_curve_transformation_file[1]
        self.coefficient_df = coefficient_file
        self.convertion_ratio_df = self.convertion_ratio_df[
            self.convertion_ratio_df["X_YEAR"] == 2023
        ]
        self.idvs = idvs
        self.group_constraints = group_constraints
        total_n_ieq_constr = (1 + len(group_constraints)) * 2

        super().__init__(
            n_var=len(xl), n_obj=2, xl=xl, xu=xu, n_ieq_constr=total_n_ieq_constr
        )

    def _evaluate(self, x, out, *args, **kwargs):

        data_df = pd.DataFrame([x])
        data_df.columns = self.idvs
        converted_df = convert_spends_to_impression_clicks(
            data_df.copy(), self.convertion_ratio_df
        )
        transformed_df_1 = transform(
            self.s_curve_df_outcome1, converted_df, idvs=list(converted_df.columns)
        )
        transformed_df_2 = transform(
            self.s_curve_df_SU, converted_df, idvs=list(converted_df.columns)
        )

        preds_1 = model_results(
            mean_scaling_df=self.mean_scaling_df,
            data_df=transformed_df_1,
            coefficient_df=self.coefficient_df,
            dv=self.dvs[0],
        )

        preds_2 = model_results(
            mean_scaling_df=self.mean_scaling_df,
            data_df=transformed_df_2,
            coefficient_df=self.coefficient_df,
            dv=self.dvs[1],
        )

        out["F"] = [-np.exp(preds_1[0]), -np.exp(preds_2[0])]

        ineq_cons = []
        budget_constraint = sum(x) - self.budget
        ineq_cons.append(budget_constraint)
        ineq_cons.append(budget_constraint)

        for constraint in self.group_constraints.items():
            sum_of_cons_var = sum_over_solution_idvs(data_df, constraint[1]["var_list"])
            if constraint[0][2] == "Cap":
                ineq_cons.append(sum_of_cons_var - constraint[1]["value"])
                ineq_cons.append(sum_of_cons_var - constraint[1]["value"])
            if constraint[0][2] == "Min":
                ineq_cons.append(-sum_of_cons_var + constraint[1]["value"])
                ineq_cons.append(-sum_of_cons_var + constraint[1]["value"])

        out["G"] = ineq_cons


def NSGA(
    budget,
    lower_bounds,
    upper_bounds,
    period_year,
    period_type,
    split_budget_proportion,
    group_constraints,
):

    termination = DefaultSingleObjectiveTermination(n_max_gen=40)

    algorithm = NSGA2(
        pop_size=40,
        n_offsprings=10,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True,
    )

    solution = upper_bounds.copy()
    convergences = []

    split = -1
    for column in solution.columns:
        split = split + 1
        lower_bounds[column] = lower_bounds[column].astype(int)
        upper_bounds[column] = upper_bounds[column].apply(np.ceil).astype(int)

        lower = list(lower_bounds[column].values)
        upper = list(upper_bounds[column].values)

        if lower == upper:
            continue
        transformation_file = []
        transformation_file.append(
            pd.DataFrame.from_records(scenario_dao.get_ad_stocks_what_if_FTB())
        )
        transformation_file.append(
            pd.DataFrame.from_records(scenario_dao.get_ad_stocks_what_if_SU())
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
            s_curve_transformation_file=transformation_file,
            group_constraints=constraints_subset,
        )

        res = minimize(problem, algorithm, termination, seed=1, verbose=True)

        x_results = res.X
        y_results = res.F

        if x_results is None:
            convergence = False
        else:
            # choose one solution among various pareto solutions
            convergence = True
            obj_max = 1
            y_best_results = []
            x_best_results = []
            print(x_results)
            print(y_results)

            if len(x_results) > 1:
                # print(y_results)
                # print(y_results.argmin(axis=0))
                max_row = y_results.argmin(axis=0)[obj_max]
            else:
                max_row = 0
            x_best_results = x_results[max_row]
            # y_best_results = y_results[max_row]
            if x_best_results is not None:
                x_best_results = [x * number_of_weeks for x in x_best_results]
                solution[column] = x_best_results

        convergences.append(convergence)

    x = np.round(solution.values.tolist(), decimals=0)
    return x, 0, np.all(convergences)
