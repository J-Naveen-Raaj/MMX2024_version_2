# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd


def prod_log_x_mul_betas_multi(X, betas):
    """
    Function to get product of x raise to beta (elasticity) modelwise by time period

    Parameters
    ----------
    X : matrix-like (2-D); `numpy.array`
        Spends by variable (index) and period (columns).

    betas : matrix-like (2-D); `pandas.DataFrame`
        Elasticities by models for each spend variable.
        Index of `betas` are the spend variables.
        Columns are `pandas.MultiIndex` with levels in the order outcome - segment - geo.
        In case the models are not at geo level, only value at the last level will be 'Coefficient'.

    Returns
    -------
    Y : matrix-like (2-D); `numpy.array`
        If the shape of `X` is (n, p) and the shape of `betas` is (n, m), where
        n = number of variables, p = number of time periods and m = number of models,
        the shape of `Y` will be (m, p)
    """
    return np.matmul(np.log(X).T, betas).T


def get_obj_func(
    obj_list, coeffs_mktg_simpl, outcome_totals, refc_scenario, X_init, pos_unlocked
):
    """
    Generate objective function based on the inputs

    Parameters
    ----------
    obj_list : list
        List of tuples in the form of `(outcome, segment)` for the objective to maximize.

    coeffs_mktg_simpl : pandas.DataFrame
        DataFrame of elasticities with index as spend variables and columns as model (outcome, segment).

    outcome_totals : pandas.DataFrame
        Outcome totals by model x period.

    refc_scenario : pandas.DataFrame
        Reference calendar spends for all variables by period.

    X_init : `numpy.array`
        Spend data for all variable. Must be from feasible set.

    pos_unlocked : list
        Indices of unlocked variables in X_init and related spend data structures

    Returns
    -------
    obj_func : function
        Function to be used inside GP. Calculates the outcome for the given spend and also returns gradient at that point.

    """
    # outcome = alpha * y_marketing
    alpha = []
    coeff_list = []
    ## Calculating slope and defining bounds
    for k in range(0, len(obj_list)):
        # Defining fixed parameters
        number_tp = refc_scenario.shape[0]
        number_qtrs = refc_scenario.shape[1]
        # Selecting coefficients for the selected objetive
        obj = obj_list[k]
        coeff_mean = coeffs_mktg_simpl.groupby(axis=1, level=[0, 1]).mean()[obj].values
        # coeff_mean = coeffs_mktg_simpl.mean(axis=1, level=[0, 1])[obj_list[k]].values
        # Repating coefficient values across 4 quarters
        coeff_list.append(np.repeat(coeff_mean, number_qtrs, 0))
        # Actuals for the selected objective
        log_y_actual = np.log1p(outcome_totals.loc[obj_list[k], :].values)
        # Refc_Scenario Sum
        refc_qtr_sum = (
            prod_log_x_mul_betas_multi(refc_scenario.values + 1, coeff_mean)
        ).T
        # Actual Spend for each touchpoint
        refc_scenario.fillna(0, inplace=True)
        # Adding a multilier apha to account for different weights for different outcome*segment*quarter
        alpha.append(np.array(list(log_y_actual / refc_qtr_sum) * number_tp))

    def obj_func(x):
        X_init[pos_unlocked] = x

        slope = 0
        y_predicted = 0

        for k in range(0, len(obj_list)):
            # calculating (x+1)^Beta
            # values_pow_beta = np.power(X_init + 1, coeff_list[k])
            values_prod_beta = np.log1p(X_init) * coeff_list[k]
            quarter_sum = []
            # quarter wise sum
            for qtr in range(0, number_qtrs):
                # quarter_sum.append(values_pow_beta[qtr::number_qtrs].prod())
                quarter_sum.append(values_prod_beta[qtr::number_qtrs].sum())
            quarter_sum_arr = np.array(quarter_sum * number_tp)
            # Slope for each touchpoint for each quarter -> will be used as objective function's coefficients
            slope_outcome_k = (
                alpha[k] * (quarter_sum_arr / (X_init + 1)) * coeff_list[k]
            )
            # Calculating y_predicted
            y_predict_k = (alpha[k] * quarter_sum_arr)[0:number_qtrs].sum()
            # Adding slopes across all objectives to get final slope
            slope = slope + slope_outcome_k
            y_predicted = y_predict_k + y_predicted

        return slope[pos_unlocked], y_predicted

    return obj_func
