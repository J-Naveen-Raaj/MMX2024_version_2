# -*- coding: utf-8 -*-
from typing import List

import numpy as np
import pandas as pd


def apply_adstock(x: List, max_memory: int, decay: float) -> pd.Series:
    """
    Create adstock transformation for a given array with specified cutoff and decay.

    Parameters
    ----------
    x : List[float]
        The input array.
    max_memory : int
        The cutoff for the adstock transformation.
    decay : float
        The decay factor for the feature.

    Returns
    -------
    pd.Series
        The
        ed column.
    """
    # code reference from https://github.com/sibylhe/mmm_stan/blob/main/mmm_stan.py

    adstocked_x = []

    if max_memory != 0:
        x = np.append(np.zeros(max_memory - 1), x)

        weights = np.zeros(max_memory)
        for j in range(max_memory):
            weight = decay ** ((j) ** 2)
            weights[max_memory - 1 - j] = weight

        for i in range(max_memory - 1, len(x)):
            x_array = x[i - max_memory + 1 : i + 1]
            xi = sum(x_array * weights)
            adstocked_x.append(xi)

    else:
        for i in x:
            if len(adstocked_x) == 0:
                adstocked_x.append(i)
            else:
                adstocked_x.append(i + decay * adstocked_x[-1])
    return adstocked_x