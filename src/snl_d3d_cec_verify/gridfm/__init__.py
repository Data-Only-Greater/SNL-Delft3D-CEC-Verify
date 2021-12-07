# -*- coding: utf-8 -*-

from __future__ import annotations

import numpy as np
from shapely.geometry import box # type: ignore

from ..types import Num, StrOrPath
from .writer import write2D
from .mesh2d import Rectangular


def write_gridfm_rectangle(path: StrOrPath,
                           dx: Num,
                           dy: Num,
                           x0: Num = 0,
                           x1: Num = 18,
                           y0: Num = 1,
                           y1: Num = 5):
    
    poly = box(x0, y0, x1, y1)
    mesh = Rectangular()
    mesh.generate_within_polygon(poly, dx, dy)
    mesh.altitude_constant(np.nan)
    write2D(mesh, str(path))
