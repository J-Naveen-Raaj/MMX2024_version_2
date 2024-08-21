# -*- coding: utf-8 -*-
"""
Constans file

"""

# List of Months
MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

# List of Quarters
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

# List of all customer segments
ALL_SEGS = ["Rakuten"]

# List of all geos
ALL_GEOS = ["US"]

# Date Column
DATE_COL = "X_DT"

# Customer Segment Column
SEG_COL = "X_SEG"

# Geo Column
GEO_COL = "X_GEO"

# Outcome Variables
OUTCOME_VARS = ["outcome2", "outcome1"]

# Dictionary for all objectives to be maximized
DICT_OBJECTIVES = {
    "outcome1": {"outcome1": ["Rakuten"]},
    "outcome2": {"outcome2": ["Rakuten"]},
    "outcome1 & outcome2":{"outcome1": ["Rakuten"],"outcome2": ["Rakuten"]}
}


