# -*- coding: utf-8 -*-

from __future__ import annotations

import numpy as np
from shapely.geometry import box

from ..types import StrOrPath
from .writer import write2D
from .mesh2d import Rectangular


def write_gridfm_rectangle(path: StrOrPath,
                           dx: float,
                           dy: float,
                           x0: float = 0.,
                           x1: float = 18.,
                           y0: float = 1.,
                           y1: float = 5.):
    
    poly = box(0, 1, 18, 5)
    mesh = Rectangular()
    mesh.generate_within_polygon(poly, dx, dy)
    mesh.altitude_constant(np.nan)
    write2D(mesh, str(path))
