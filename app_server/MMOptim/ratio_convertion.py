# -*- coding: utf-8 -*-
import pandas as pd

from app_server.MMOptim.constants import DATE_COL, GEO_COL, SEG_COL


def get_spend_totals(data, spend_vars, spend_scaling_factor):
    """
    Get marketing spend totals for a given data and variable levels
    """
    spend_totals = data[spend_vars].sum(axis=0)
    if spend_scaling_factor is not None:
        spend_totals /= spend_scaling_factor
    return spend_totals

def get_spend_totals_by_group(data, spend_vars, spend_scaling_factor, group_cols):
    """
    Get marketing spend totals by groups
    """
    if group_cols:
        spend_totals_grouped = (
            data.groupby(group_cols)
            .apply(lambda x: get_spend_totals(x, spend_vars, spend_scaling_factor))
            .T
        )
    else:
        spend_totals_grouped = get_spend_totals(data, spend_vars, spend_scaling_factor)
    return spend_totals_grouped
