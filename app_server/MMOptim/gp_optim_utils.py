# -*- coding: utf-8 -*-
"""
For Running Optimization

"""

import math

import numpy as np
from scipy.optimize import linprog


def get_init_sol(lower_bounds, upper_bounds, budget, constraints, method="simplex"):
    """
    Get an initial solution from feasible set based on the provided set of bounds and constraints

    Parameters
    ----------
    lower_bounds, upper_bounds : pandas.DataFrame
        Base scenario spends, lower and upper bounds for all variables by period.

    constraints : dict
        Dictionary containing the information for additional constraints.

    budget : float
        Total budget for optimization.

    Returns
    -------

    X : `numpy.array`
        The spend plan generated via linprog solver based on the provided bounds and constraints

    A_ub : matrix-like (2-D); `numpy.array`
        Inequality constraint matrix

    b_ub :
        Inequality value matrix

    lb, ub : `numpy.array`
        Long (Flat) format lower bound and upper bound

    lock_cons_index : list
        Stores indices of locked constraints to be used by GP to force them tight

    """
    # Bounds
    lb = np.round(lower_bounds.values.flatten(), decimals=0)
    ub = np.round(upper_bounds.values.flatten(), decimals=0)

    # Constraints
    n_rows, n_cols = lower_bounds.shape
    print(n_rows, n_cols)
    n_vars = n_cols * n_rows
    # Initialize A_ub (constraint matrix) and b_ub
    A_ub, b_ub = [], []
    # Initializing A_eq, b_eq with 0 data to pass a non-empty list to linprog solver
    A_eq, b_eq = [np.zeros(n_vars)], [0]

    # Add total budget as a cap constraint
    A_ub.append(np.ones(n_vars))
    b_ub.append(math.floor(budget["total"]))
    # Create an index of locked constraints, to be used later by GP
    lock_cons_index = []
    # A counter is used to keep track of constraint index in the loop
    # Initializing with 1 since A_ub already has "total budget" as a constraint.
    index_counter = 1

    # Iterate through each constraint fill the constraint matrix A_ub and b_ub accordingly
    for key in constraints.keys():
        cons = constraints[key]
        a = np.zeros(n_vars)
        pos = cons["pos"]
        pos_flat = pos[0] * n_cols + pos[1]
        a[pos_flat] = 1

        if cons["type"] == "Lock":
            # If single variable group constraint, convert to bounds
            if len(pos_flat) == 1:
                lb[pos_flat] = cons["value"]
                ub[pos_flat] = cons["value"]
                print("Converting single variable group constraint to bounds", key)
                continue

            A_ub.append(a)
            b_ub.append(cons["value"])

            # Filling in A_eq (equality constraint matrix) as well for lock type constraint
            # This helps the linprog solver provide accurate and feasible solution
            A_eq.append(a)
            b_eq.append(cons["value"])

            lock_cons_index.append(index_counter)

        if cons["type"] == "Cap":
            A_ub.append(a)
            b_ub.append(cons["value"])

        # multiply both sides by -1 to convert ">" (greater than inequality) to "<" (less than inequality)
        if cons["type"] == "Min":
            A_ub.append(-1 * a)
            b_ub.append(-1 * cons["value"])

        index_counter += 1

    A_ub = np.atleast_2d(A_ub) if len(A_ub) else None
    b_ub = np.atleast_1d(b_ub) if len(b_ub) else None

    # Decimal conversion
    # try:
    #     b_ub = np.round(b_ub, decimals=0)
    #     b_eq = np.round(b_eq, decimals=0)
    # except:
    #     b_ub = b_ub
    #     b_eq = b_eq
    try:
        b_ub = np.round(b_ub, decimals=0)
        b_eq = np.round(b_eq, decimals=0)
    except (ValueError, TypeError) as e:
        logging.error(f"Error during rounding: {e}")
        # Optionally re-raise the exception if you want to halt execution
        raise
    ## Intial point for gradient projection
    ## Find a few points in feasible set
    ## Take an average of the points as starting point to avoid starting at edges.
    ## As the feasible space is convex, the mid point (or average) will be in feasible set

    bounds_lp = list(zip(lb, ub))

    c1 = np.tile([1, 0], int(n_vars / 2))
    c2 = np.tile([0, 1], int(n_vars / 2))

    c3 = np.tile([0, 0, 1, 1], int(n_vars / 4))
    c4 = np.tile([1, 1, 0, 0], int(n_vars / 4))

    c5 = np.tile([0, 1, 1, 0], int(n_vars / 4))
    c6 = np.tile([1, 0, 0, 1], int(n_vars / 4))

    linprog_results = np.zeros(n_vars)

    c_range = [-c1, -c2, -c3, -c4, -c5, -c6, c1, c2, c3, c4, c5, c6]

    X = None
    # for c in c_range:
    #     linprog_res_ci = linprog(
    #         c=c,
    #         A_eq=A_eq,
    #         b_eq=b_eq,
    #         A_ub=A_ub,
    #         b_ub=b_ub,
    #         bounds=bounds_lp,
    #         method=method,
    #         options={"disp": True, "tol": 0.53},
    #     )
    #     linprog_results += linprog_res_ci["x"]

    # X = linprog_results / len(c_range)

    return X, A_ub, b_ub, lb, ub, lock_cons_index


def process_bounds(lb, ub, A_ub, b_ub, budget):
    """
    Process the bounds further to remove the effect of lock variables.
    Then adds bounds as a constraint to constraint matrix A_ub for GP

    Parameters
    ----------
    lb, ub : `numpy.array`
        Long (Flat) format lower bound and upper bound

    A_ub : matrix-like (2-D); `numpy.array`
        Inequality constraint matrix

    b_ub :
        Inequality value matrix

    budget : float
        Total budget for optimization.

    Returns
    -------

    A_ub : matrix-like (2-D); `numpy.array`
        Modified inequality constraint matrix adjusted for lock variables

    b_ub : `numpy.array`
        Modified Inequality value matrix adjusted for lock variables

    pos_locked : list
        Indices of locked variables in related spend data structures

    pos_unlocked : list
        Indices of unlocked variables in X_init and related spend data structures

    all_var_locked_cons : list
        Indices of constraints from A_ub where all the variables are themselves locked

    """

    # Get lock and unlocked variable indices
    pos_locked = [i for i in range(len(lb)) if lb[i] == ub[i]]
    pos_unlocked = [i for i in range(len(lb)) if lb[i] != ub[i]]

    unlocked_var_count = len(pos_unlocked)

    # Remove lock variables total from "total budget"
    b_ub[0] = math.floor(budget["total"])

    # Removing lock variables and their total from constraint matrix and constraint value list
    for i in range(len(A_ub)):
        indices = list(map(int, A_ub[i, pos_locked]))
        zipped_pairs = zip(indices, pos_locked)
        indices_to_sum = [p for i, p in zipped_pairs if i == 1]
        sum_to_remove = lb[indices_to_sum].sum()
        b_ub[i] -= sum_to_remove

    A_ub = np.delete(A_ub, pos_locked, axis=1)

    ## Add lower bounds and upper bounds as constraints to A_ub and corresponding value to b_ub
    # Convert numpy array to list
    # It's easier to append to list in python than to numpy array
    A_ub = list(A_ub)
    b_ub = list(b_ub)

    ub = ub[pos_unlocked]
    lb = lb[pos_unlocked]

    # Add lower bounds
    for i in range(len(pos_unlocked)):
        lb_template = np.zeros(unlocked_var_count)
        lb_template[i] = -1
        A_ub.append(lb_template)
        b_ub.append(-1 * lb[i])

    # Add upper bounds
    for i in range(len(pos_unlocked)):
        ub_template = np.zeros(unlocked_var_count)
        ub_template[i] = 1
        A_ub.append(ub_template)
        b_ub.append(ub[i])

    # Convert back to numpy ndarray
    A_ub = np.atleast_2d(A_ub)
    b_ub = np.atleast_1d(b_ub)

    # If all variables for a group constraint are locked, delete it as a constraint
    all_var_locked_cons = np.where(A_ub.sum(axis=1) == 0)
    A_ub = np.delete(A_ub, all_var_locked_cons, axis=0)
    b_ub = np.delete(b_ub, all_var_locked_cons, axis=0)

    return A_ub, b_ub, pos_locked, pos_unlocked, all_var_locked_cons
