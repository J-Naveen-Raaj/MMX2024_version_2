# -*- coding: utf-8 -*-
# ==============================================================================
# Functions related to Waterfall Chart
# ==============================================================================

# Function: getBarStart -------------------------------------------------------
"""
Function to dynamically get the start point for waterfall chart base and total bar
"""
from math import log10

"""
Function to prepare waterfall chart data for D3.js
"""


def getWaterfallChartData(base, incremental, total, start_point = 0, add_gap = True, round_digits = 1):
    '''
    base = {'name': base_name, 'value': base_value}
    incremental = {'names': [name1, name2, name3, ...]
                   'values': [value1, value2, value3, ...]}
    total = {'name': total_name, 'value': total_value}
    '''
    try:
        chart_data = []
        cum = 0
        # Base
        if base is not None:
            chart_data.append({ "class": "base", "name": base["name"], "start": start_point,
                                "end": round(base["value"], round_digits),
                                "value": round(base["value"], round_digits) })
            cum += base["value"]
            # cum = round(cum, round_digits)
        # Incremental
        for n, v in zip(incremental["names"], incremental["values"]):
            chart_data.append({ "class": "positive" if v >= 0 else "negative", "name": n, "start": cum,
                                "end": round(cum + v, round_digits), "value": round(v, round_digits) })
            cum += v
            # cum = round(cum, round_digits)
        # Total
        if total is not None:
            # Gap
            if add_gap:
                chart_data.append(
                        { "class": "negative", "name": "Gap", "start": cum, "end": round(total["value"], round_digits),
                          "value": round(total["value"] - cum, round_digits) })
            if (total["value"] == 0):
                chart_data.append(
                        { "class": "total", "name": total["name"], "start": start_point, "end": cum, "value": cum })
            else:
                chart_data.append({ "class": "total", "name": total["name"], "start": start_point,
                                    "end": round(total["value"], round_digits),
                                    "value": round(total["value"], round_digits) })
        else:
            chart_data.append({ "class": "total", "name": "Total", "start": start_point, "end": cum, "value": cum })
        return chart_data

    except Exception as e:
        raise Exception("Exception occurred in getWaterfallChartData() function. ", e)

