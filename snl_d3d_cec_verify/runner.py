# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING, Union
from pathlib import Path

import numpy as np
from shapely.geometry import box

from .cases import Template
from .copier import copy
from .gridfm import Rectangular, write2D

if TYPE_CHECKING:
    from .cases import CaseStudy


class Runner:
    
    def __init__(self, template_path: Union[str, Path]):
        self._template_path = template_path
        return
    
    def make_case_files(self, case: CaseStudy,
                              project_path: Union[str, Path]):
        
        if len(case) != 1:
            raise ValueError("Case study must have length one")
        
        # Copy templated files
        data = {field: value.value
                    for field, value in zip(case.fields, case.values)
                                            if isinstance(value, Template)}
        
        copy(self._template_path, project_path, data)
        make_gridfm_file(Path(project_path) / "input" / "FlowFM_net.nc",
                         case.dx,
                         case.dy)


def make_gridfm_file(path: Union[str, Path],
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
