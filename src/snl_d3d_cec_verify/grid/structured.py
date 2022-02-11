# -*- coding: utf-8 -*-

from __future__ import annotations

import math
from typing import Callable, List, Sequence

from ..types import Num


def _make_eta(x: Sequence[Num],
              y: Sequence[Num],
              func: Callable[[Sequence[Num],
                              Sequence[Num],
                              int,
                              int,
                              int], Sequence[Num]]) -> List[str]:
    
    msgs = []
    
    for i in range(len(y)):
        
        msg = f' ETA={i + 1:>5}   '
        
        for j in range(math.ceil(len(x) / 5)):
            
            nnums = len(x[5 * j:5 * (j + 1)])
            nums = func(x, y, i, j, nnums)
            
            fmt = '{:.17E}   ' * (nnums - 1) + '{:.17E}'
            msg += fmt.format(*nums)
            msgs.append(msg)
            msg = ' ' * 13
    
    return msgs


def make_eta_x(x: Sequence[Num],
               y: Sequence[Num]) -> List[str]:
    makex = lambda x, y, i, j, nnums: x[5 * j:5 * (j + 1)]
    return _make_eta(x, y, makex)


def make_eta_y(x: Sequence[Num],
               y: Sequence[Num]) -> List[str]:
    makey = lambda x, y, i, j, nnums: [y[i]] * nnums
    return _make_eta(x, y, makey)
