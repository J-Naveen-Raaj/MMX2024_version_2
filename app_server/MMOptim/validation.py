# -*- coding: utf-8 -*-
"""
Validations for optimization

"""

# %%
import numpy as np
# import pandas as pd
from scipy.optimize import linprog


## User defined error
class Error(Exception):
    """Base class for other exceptions"""

    pass


class ValidationError(Error):
    """Raised when the basic validation fails"""

    def __init__(self, message, error=None, warning=None):
        self.message = message

    def to_dict(self):
        rv = dict()
        rv["message"] = self.message
        return rv


class FeasibilityError(Error):
    """Raised when the scenario is infeasible"""

    def __init__(self, message):
        self.message = message

    def to_dict(self):
        rv = dict()
        rv["message"] = self.message
        return rv


# %%
def basic_validation(base_scenario, lower_bounds, upper_bounds, constraints, budget):
    ## Set counters for error and warnings
    """

    Parameters
    ----------
    base_scenario
    lower_bounds
    upper_bounds
    constraints
    budget

    Returns
    -------

    """
    error_report = []
    warn_report = []

    ## RULE 1. total budget < sum of lower bounds
    rule = budget["total"] < np.sum(lower_bounds.values)

    if rule == True:
        error_message = "ERROR: Total Budget < Sum of Lower Bounds"
        error_report.append(error_message)
        print(budget["total"], np.sum(lower_bounds.values))
        print(error_message)

    ## RULE 2. total budget > sum of upper bounds
    rule = budget["total"] > np.sum(upper_bounds.values)
    if rule == True:
        warn_message = "WARNING: Total Budget > Sum of Upper Bounds"
        warn_report.append(warn_message)
        print(budget["total"], np.sum(upper_bounds.values))
        print(warn_message)

    ## RULE 3. upper_bounds < lower_bounds
    rule = (upper_bounds < lower_bounds).stack()
    rule_violate_list = rule.index[rule].tolist()
    for item in rule_violate_list:
        error_message = "ERROR in {0} bounds: Upper Bound < Lower Bound".format(item)
        error_report.append(error_message)
        print(error_message)

    ## RULE 4. base_scenario < lower_bounds
    rule = (base_scenario < lower_bounds).stack()
    rule_violate_list = rule.index[rule].tolist()
    for item in rule_violate_list:
        warn_message = "WARNING in {0} bounds: Base Spend < Lower Bound".format(item)
        warn_report.append(warn_message)
        print(warn_message)

    ## RULE 5. base_scenario > upper_bounds
    rule = (base_scenario > upper_bounds).stack()
    rule_violate_list = rule.index[rule].tolist()
    for item in rule_violate_list:
        warn_message = "WARNING in {0} bounds: Base Spend > Upper Bound".format(item)
        warn_report.append(warn_message)
        print(warn_message)

    ## RULE 6. ForEach{SumOf(subset of X_lb)} > Constraint amount
    ## Should check for all combinations or can check only for the largest as well
    ## i.e. check for sum of all lower bounds of all variables
    ## For Lock & Cap cases only

    for key, cons in constraints.items():
        #  if((cons['type'] == 'Lock') or (cons['type'] == 'Cap')):
        if cons["type"] in ["Lock", "Cap"]:
            if np.sum(lower_bounds.values[cons["pos"]]) > cons["value"]:
                message = "ERROR in {0} {1} constraint: minimum possible value > constraint value"
                error_message = message.format(key, cons["type"])
                error_report.append(error_message)
                print(error_message)

                ## RULE 7. SumOf(X_ub) < Constraint amount  ## For lock and min cases  #        if((cons['type'] == 'Lock') or (cons['type'] == 'Min')):
        if cons["type"] in ["Lock", "Min"]:
            if np.sum(upper_bounds.values[cons["pos"]]) < cons["value"]:
                message = "ERROR in {0} {1} constraint: maximum possible value < constraint value"
                error_message = message.format(key, cons["type"])
                error_report.append(error_message)
                print(error_message)

    msg = "Validation finished with {ec} errors and {wc} warnings".format(
        ec=len(error_report), wc=len(warn_report)
    )
    #    print(msg)

    if len(error_report):
        raise ValidationError(msg, error_report, warn_report)
    else:
        return warn_report


# %%


def feasibility_check(base_scenario, lower_bounds, upper_bounds, constraints, budget):
    """

    Parameters
    ----------
    base_scenario
    lower_bounds
    upper_bounds
    constraints
    budget

    Returns
    -------

    """
    n_rows, n_cols = lower_bounds.shape
    n_vars = n_cols * n_rows

    c = np.zeros(n_vars)

    lb = lower_bounds.values.flatten()
    ub = upper_bounds.values.flatten()
    bounds = list(zip(lb, ub))

    A_ub, b_ub = [], []
    A_eq, b_eq = [], []

    A_ub.append(np.ones(n_vars))
    b_ub.append(budget["total"])

    for cons in constraints.values():
        a = np.zeros(n_vars)
        pos = cons["pos"]
        pos_flat = pos[0] * n_cols + pos[1]
        a[pos_flat] = 1

        if cons["type"] == "Lock":
            A_eq.append(a)
            b_eq.append(cons["value"])

        if cons["type"] == "Cap":
            A_ub.append(a)
            b_ub.append(cons["value"])

        # multiply both sides by -1 to convert ">" (greater than inequality) to "<" (less than inequality)
        if cons["type"] == "Min":
            #            a[pos_flat] *= -1
            A_ub.append(-1 * a)
            b_ub.append(-1 * cons["value"])

    A_ub = np.atleast_2d(A_ub) if len(A_ub) else None
    b_ub = np.atleast_1d(b_ub) if len(b_ub) else None
    A_eq = np.atleast_2d(A_eq) if len(A_eq) else None
    b_eq = np.atleast_1d(b_eq) if len(b_eq) else None

    linprog_res = linprog(
        c=c,
        A_eq=A_eq,
        A_ub=A_ub,
        b_eq=b_eq,
        b_ub=b_ub,
        bounds=bounds,
        method="interior-point",
    )

    ## linprog.status == 2 is infeasible, == 4 incomplete run, == 0 feasible
    if linprog_res.status == 2:
        msg = "The provided constraints result in infeasible bounds"
        raise FeasibilityError(msg)
    else:
        return True

        # %%

        ##%%  # from timeit import default_timer as timer  # from datetime import timedelta  #  ##%%  # if __name__ == '__main__':  #    basic_validation(base_scenario, lower_bounds, upper_bounds, constraints, budget)  #    n= 1  #    start = timer()  #    for i in range(n):  #        a = feasibility_check(base_scenario, lower_bounds, upper_bounds, constraints, budget)  #    end = timer()  #    print("Time taken for ",n, "runs - ", timedelta(seconds=end - start))
