# -*- coding: utf-8 -*-

from __future__ import annotations

import numpy as np
from shapely.geometry import box # type: ignore

from .fm import Rectangular as RectangularFM
from .fm import write as writeFM
from .structured import write_rectangle as write_structured_rectangle
from ..types import AnyByStrDict, Num, StrOrPath
from .._docs import docstringtemplate

__all__ = ["write_fm_rectangle", "write_structured_rectangle"]


@docstringtemplate
def write_fm_rectangle(path: StrOrPath,
                       dx: Num,
                       dy: Num,
                       x0: Num = 0,
                       x1: Num = 18,
                       y0: Num = 1,
                       y1: Num = 5) -> AnyByStrDict:
    """Create a rectangular Delft3D flexible mesh grid, in a rectangular 
    domain (``x0``, ``y0``, ``x1``, ``y1``), and save to the given path, in
    netCDF format.
    
    :param path: destination path for the grid file
    :param dx: grid spacing in the x-direction, in metres
    :param dy: grid spacing in the y-direction, in metres
    :param x0: minimum x-value, in metres, defaults to {x0}
    :param x1: maximum x-value, in metres, defaults to {x1}
    :param y0: minimum y-value, in metres, defaults to {y0}
    :param y1: maximum y-value, in metres, defaults to {y1}
    
    """
    
    poly = box(x0, y0, x1, y1)
    mesh = RectangularFM()
    mesh.generate_within_polygon(poly, dx, dy)
    mesh.altitude_constant(np.nan)
    writeFM(mesh, str(path))
    
    return {}
