# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Tuple, TYPE_CHECKING

import xarray as xr

from .edges import Edges
from .faces import Faces
from ..types import StrOrPath

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt


class Result:
    
    def __init__(self, map_path: StrOrPath):
        self._map_path = map_path
        self._x_lim = get_x_lim(map_path)
        self._y_lim = get_y_lim(map_path)
        self._times: npt.NDArray[np.datetime64] = get_step_times(map_path)
        self._edges: Edges = Edges(map_path)
        self._faces: Faces = Faces(map_path, self._x_lim[1])
    
    @property
    def x_lim(self):
        return self._x_lim
    
    @property
    def y_lim(self):
        return self._y_lim
    
    @property
    def times(self):
        return self._times
    
    @property
    def edges(self):
        return self._edges
    
    @property
    def faces(self):
        return self._faces
    
    def __repr__(self):
        return f"Result(map_path={repr(self._map_path)})"


def get_x_lim(map_path: StrOrPath) -> Tuple[float, float]:
    with xr.open_dataset(map_path) as ds:
        x = ds.mesh2d_node_x.values
    return (x.min(), x.max())


def get_y_lim(map_path: StrOrPath) -> Tuple[float, float]:
    with xr.open_dataset(map_path) as ds:
        y = ds.mesh2d_node_y.values
    return (y.min(), y.max())


def get_step_times(map_path: StrOrPath) -> npt.NDArray[np.datetime64]:
    with xr.open_dataset(map_path) as ds:
        time = ds.time.values
    return time
