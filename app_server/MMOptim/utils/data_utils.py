# -*- coding: utf-8 -*-
"""
Created on Tue May 28 16:23:58 2019

@author: tamal.panja
"""

import numpy as np
import pandas as pd


def filter_data_by_col_values(data, col, values, isin = True):
    """
    Filter data by a column where the values of the given column are in a given list of values 
    / not in the list
    """
    if isin:
        data_sub = data.loc[data[col].isin(values)]
    else:
        data_sub = data.loc[~data[col].isin(values)]
    return data_sub


def get_array_position(df, select_index = None, select_columns = None):
    """
    Get the position of cells in DataFrame by selected index and columns.
    
    Parameters
    ----------
    df : pandas.DataFrame
    
    select_index : array-like; list
        List of index values in df. If it is None, all index of the DataFrame will be considered.
    
    select_columns : array-like; list
        List of columns in df. If it it None, all columns of the DataFRame will be considered.
    
    Returns
    -------
    pos : Array positions of the cells in selected index and columns.
    """
    if select_index is None:
        select_index = df.index
    if select_columns is None:
        select_columns = df.columns
    idx_pos = np.where(df.index.isin(select_index))
    col_pos = np.where(df.columns.isin(select_columns))
    grid = np.meshgrid(idx_pos, col_pos)
    pos = tuple([arr.T.flatten() for arr in grid])
    return pos


def add_subtotals(x, subtotal_levels = None, subtotal_name = ''):
    """
    Add sub totals to a MultiIndex Series or DataFrame.
    
    Parameters
    ----------
    x : MultiIndex Series or DataFrame
    
    subtotal_levels : list
        List of integers specifying the MultiIndex levels at which subtotals to be calculated. 
        If None, subtotals will be calculated at every level. Default None.
    
    subtotal_name : str
        Name to be shown at subtotal levels. Default ''.
    
    Returns
    -------
    x_with_subtotals : MultiIndex Series or DataFrame
        Series or DataFrame with subtotals added at desired levels.
    """
    extend_index = lambda idx, new, rep: (idx if isinstance(idx, tuple) else (idx,)) + (new,) * rep
    n_levels = x.index.nlevels
    if subtotal_levels is None:
        subtotal_levels = range(n_levels)
    all_subtotals = []
    for i in subtotal_levels:
        if i > 0:
            subtotal = x.sum(axis = 0, level = list(range(i)))
            nrep = n_levels - subtotal.index.nlevels
            subtotal.index = [extend_index(idx, subtotal_name, nrep) for idx in subtotal.index]
        else:
            subtotal = x.sum(axis = 0, level = None)
            subtotal_index = (subtotal_name,) * n_levels
            if np.isscalar(subtotal):
                subtotal = pd.Series(subtotal, index = [subtotal_index])
            else:
                subtotal = subtotal.to_frame(subtotal_index).T
        all_subtotals.append(subtotal)
    x_with_subtotals = x.copy()
    for subtotal in all_subtotals:
        x_with_subtotals = x_with_subtotals.append(subtotal)
    x_with_subtotals = x_with_subtotals.sort_index()
    return x_with_subtotals
