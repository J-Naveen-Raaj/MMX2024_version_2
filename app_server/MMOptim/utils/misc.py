# -*- coding: utf-8 -*-
"""
Created on Tue May 28 18:15:06 2019

@author: tamal.panja
"""


def match_pos(x, y):
    """
    Find the index of elements of x in y; for elements of x not in y the value will be -1.
    """
    pos = [y.index(x_i) for x_i in x]
    return pos
