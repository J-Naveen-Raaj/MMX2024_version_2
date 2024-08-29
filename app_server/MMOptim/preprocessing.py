# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from app_server.MMOptim.constants import DATE_COL, OUTCOME_VARS, SEG_COL

WEEK_END_DATE_COL = "Week end Date"


def filter_data(all_data, ref_calendar, period_type, start_period, end_period):
    """
    Filter data for optimization time period.

    Parameters
    ----------
    all_data : pandas.DataFrame
        Complete data.

    ref_calendar : pandas.DataFrame
        Reference calendar for the optimization.

    period_type : str
        Type of the period to filter data by. Can take one of the two inputs: "MONTH" or "QUARTER".

    start_period, end_period : int
        Numeric (integer) input for start/end period.
        Should be one of 1 to 4 (for `period_type` 'QUARTER') or 1 to 12 (for `period_type` 'MONTH').
        Note that, `end_period` should be greater than or equal to `start_period`,
        otherwise filered data will be blank.

    Returns
    -------
    filtered_data : pandas.DataFrame
    """

    # Start and end date for optimization in reference callendar
    start_date = ref_calendar.loc[
        ref_calendar[period_type] == start_period, WEEK_END_DATE_COL
    ].min()
    end_date = ref_calendar.loc[
        ref_calendar[period_type] == end_period, WEEK_END_DATE_COL
    ].max()

    # Filter data for a given period
    data = all_data.loc[all_data[DATE_COL].between(start_date, end_date), :]
    data.reset_index(drop=True, inplace=True)

    return data

def get_ref_calendar_outcome_totals(data, ref_calendar, time_var=None):
    """
    Get outcome totals by segment x time period

    Parameters
    ----------
    time_var : str
        Can take values: 'QUARTER' | 'MONTH' | None (for overall time period)
    """
    data.rename(columns={'OUTCOME2': 'outcome2','OUTCOME1':'outcome1'}, inplace=True)
    outcome_data = pd.merge(
        ref_calendar.rename(columns={WEEK_END_DATE_COL: DATE_COL}),
        data[[DATE_COL, SEG_COL] + OUTCOME_VARS],
        on=DATE_COL,
    )
    id_vars = [SEG_COL, time_var] if time_var else [SEG_COL]
    outcome_data = outcome_data.melt(id_vars=id_vars, value_vars=OUTCOME_VARS)
    outcome_data.rename(
        columns={SEG_COL: "segment", "variable": "outcome"}, inplace=True
    )
    outcome_totals = outcome_data.pivot_table(
        values=["value"], index=["outcome", "segment"], columns=time_var, aggfunc=np.sum
    )
    return outcome_totals
