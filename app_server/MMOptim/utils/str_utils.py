# -*- coding: utf-8 -*-
"""
Created on Fri May 24 11:27:15 2019

@author: tamal.panja
"""


def str_startswith(x, prefix, values = True):
    """
    From a list of strings, get the list of strings/index which starts with a given prefix
    """
    idx = []
    vals = []
    for i in range(len(x)):
        if x[i].startswith(prefix):
            idx.append(i)
            vals.append(x[i])
    if values:
        return vals
    else:
        return idx


def str_endswith(x, suffix, values = True):
    """
    From a list of strings, get the list of strings/index which ends with a given suffix
    """
    idx = []
    vals = []
    for i in range(len(x)):
        if x[i].endswith(suffix):
            idx.append(i)
            vals.append(x[i])
    if values:
        return vals
    else:
        return idx


def str_contains(x, sub, values = True):
    """
    From a list of strings, get the list of strings/index which contains a given substring
    """
    idx = []
    vals = []
    for i in range(len(x)):
        if sub in x[i]:
            idx.append(i)
            vals.append(x[i])
    if values:
        return vals
    else:
        return idx


def str_split_by_nth_occurrence(x, sep, n = 1):
    """
    Split a string by n-th occurrence of a separator
    """
    x_splitted = x.split(sep)
    x1 = sep.join(x_splitted[:n])
    x2 = sep.join(x_splitted[n:])
    return x1, x2
