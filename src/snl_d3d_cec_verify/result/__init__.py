# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING
from pathlib import Path

import xarray as xr

from .edges import Edges
from .faces import Faces
from ..types import StrOrPath

if TYPE_CHECKING: # pragma: no cover
    import numpy as np 
    import numpy.typing as npt


class Result:
    
    def __init__(self, project_path: StrOrPath,
                       relative_map_parts: Optional[List[str]] = None):
        
        if relative_map_parts is None:
            relative_map_parts = ["output", "FlowFM_map.nc"]
        
        self._map_path = Path(project_path).joinpath(*relative_map_parts)
        self._x_lim = get_x_lim(self._map_path)
        self._y_lim = get_y_lim(self._map_path)
        self._times: npt.NDArray[np.datetime64] = get_step_times(
                                                                self._map_path)
        self._edges: Edges = Edges(self._map_path, len(self._times))
        self._faces: Faces = Faces(self._map_path,
                                   len(self._times),
                                   self._x_lim[1])
    
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


from collections.abc import Mapping
from dataclasses import dataclass

from typing import Sequence
from ..types import Num


@dataclass(frozen=True)
class Transect(Mapping):
    z: Num
    x: Sequence[Num]
    y: Sequence[Num]
    values: Optional[Sequence[Num]] = None
    
    def __post_init__(self):
        
        if len(self.x) != len(self.y):
            raise ValueError("Length of x and y must match")
        
        if self.values is not None and len(self.values) != len(self.x):
            raise ValueError("Length of values must match x and y")
    
    @classmethod
    def from_csv(path: StrOrPath):
        path = Path(StrOrPath)
    
    def __iter__(self):
        yield "z"
        yield "x"
        yield "y"
    
    def __len__(self):
        return 3
    
    def __getitem__(self, item):
        return getattr(self, item)
