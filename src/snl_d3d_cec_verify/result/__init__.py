# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import csv
import itertools
from typing import (Any,
                    Dict,
                    Hashable,
                    List,
                    Mapping,
                    Optional,
                    Tuple,
                    TYPE_CHECKING,
                    Type,
                    TypeVar,
                    Union)
from pathlib import Path
from collections import defaultdict, Sequence
from collections.abc import KeysView
from dataclasses import dataclass, field, InitVar

import numpy as np
import xarray as xr

from yaml import load
try:
    from yaml import CSafeLoader as Loader
except ImportError: # pragma: no cover
    from yaml import SafeLoader as Loader # type: ignore

from .edges import Edges
from .faces import Faces
from ..cases import CaseStudy
from ..types import Num, StrOrPath

if TYPE_CHECKING: # pragma: no cover
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


@dataclass(frozen=True, repr=False)
class Validate():
    _transects: List[Transect] = field(default_factory=list, init=False)
    case: InitVar[Optional[CaseStudy]] = None
    data_dir: InitVar[Optional[StrOrPath]] = None
    
    def __post_init__(self, case: Optional[CaseStudy],
                            data_dir: Optional[StrOrPath]):
        
        if data_dir is None:
            data_dir = mycek_data_path()
        else:
            data_dir = Path(data_dir)
        
        if not data_dir.is_dir():
            raise FileNotFoundError("Given data_dir is not a directory")
        
        turb_pos_x: Num = 0
        turb_pos_y: Num = 0
        turb_pos_z: Num = 0
        
        if case is not None:
            assert not isinstance(case.turb_pos_x, Sequence)
            assert not isinstance(case.turb_pos_y, Sequence)
            assert not isinstance(case.turb_pos_z, Sequence)
            turb_pos_x = case.turb_pos_x
            turb_pos_y = case.turb_pos_y
            turb_pos_z = case.turb_pos_z
        
        translation = (turb_pos_x, turb_pos_y, turb_pos_z)
        transects = []
        
        for item in data_dir.iterdir():
            
            if not item.is_file(): continue
            if not item.suffix == '.yaml': continue
            
            transect = Transect.from_yaml(item, translation)
            transects.append(transect)
        
        object.__setattr__(self, '_transects', transects)
    
    def __getitem__(self, item: int) -> Transect:
        return self._transects[item]
    
    def __len__(self) -> int:
        return len(self._transects)
    
    def __repr__(self):
        
        msg = "Validate("
        indent = len(msg)
        
        transect = self._transects[0]
        msg += f"0: {transect.attrs['description']}"
        
        for i, transect in enumerate(self._transects[1:]):
            
            index = i + 1
            
            msg += "\n" + " " * indent
            msg += f"{index}: {transect.attrs['description']}"
        
        msg += ")"
        
        return msg


def mycek_data_path() -> Path:
    this_dir = os.path.dirname(os.path.realpath(__file__))
    return Path(this_dir) / "mycek2014"


# Types definitions
T = TypeVar('T', bound='Transect')
Vector = Tuple[Num, Num, Num]


@dataclass(eq=False, frozen=True)
class Transect():
    z: Num = field(repr=False)
    x: npt.NDArray[np.float64] = field(repr=False)
    y: npt.NDArray[np.float64] = field(repr=False)
    data: Optional[npt.NDArray[np.float64]] = field(default=None, repr=False)
    name: Optional[str] = None
    attrs: Optional[dict[str, str]] = None
    translation: InitVar[Vector] = (0, 0, 0)
    
    def __post_init__(self, translation: Vector):
        
        if len(self.x) != len(self.y):
            raise ValueError("Length of x and y must match")
        
        if self.data is not None and len(self.data) != len(self.x):
            raise ValueError("Length of data must match x and y")
        
        z = self.z + translation[2]
        x = np.array(self.x) + translation[0]
        y = np.array(self.y) + translation[1]
        
        # Overcome limitation of frozen flag
        object.__setattr__(self, 'z', z)
        object.__setattr__(self, 'x', x)
        object.__setattr__(self, 'y', y)
        
        if self.data is None: return
        
        data = np.array(self.data)
        object.__setattr__(self, 'data', data)
    
    @classmethod
    def from_csv(cls: Type[T], path: StrOrPath,
                               name: Optional[str] = None,
                               attrs: Optional[dict[str, str]] = None,
                               translation: Vector = (0, 0, 0)) -> T:
        
        path = Path(path)
        cols = defaultdict(list)
        keys = ["x", "y", "z", "data"]
        
        with open(path) as csvfile:
            
            reader = csv.DictReader(csvfile)
            
            for row, key in itertools.product(reader, keys):
                if key in row: cols[key].append(float(row[key]))
        
        z = list(set(cols["z"]))
        data = np.array(cols.pop("data")) if "data" in cols else None
        
        if len(z) != 1:
            raise ValueError("Transect only supports fixed z-value")
        
        if attrs is None: attrs = {}
        attrs["path"] = str(path.resolve())
        
        return cls(z[0],
                   np.array(cols["x"]),
                   np.array(cols["y"]),
                   data=data,
                   name=name,
                   attrs=attrs,
                   translation=translation)
    
    @classmethod
    def from_yaml(cls: Type[T], path: StrOrPath,
                                translation: Vector = (0, 0, 0)) -> T:
        
        path = Path(path)
        
        with open(path) as yamlfile:
            raw = load(yamlfile, Loader=Loader)
        
        data = None
        name = None
        attrs = {}
        
        if "data" in raw: data = np.array(raw["data"])
        if "name" in raw: name = raw["name"]
        if "attrs" in raw: attrs = raw["attrs"]
        attrs["path"] = str(path.resolve())
        
        return cls(raw["z"],
                   x=np.array(raw["x"]),
                   y=np.array(raw["y"]),
                   data=data,
                   name=name,
                   attrs=attrs,
                   translation=translation)

    def keys(self):
        return KeysView(["z", "x", "y"])
    
    def to_xarray(self) -> xr.DataArray:
        
        keys = [f"${x}$" for x in ["z", "x", "y"]]
        coords: Mapping[Hashable, Any] = {keys[0]: self.z,
                                          keys[1]: ("dim_0", self.x),
                                          keys[2]: ("dim_0", self.y)}
        
        if self.data is None:
            return xr.DataArray([np.nan] * len(self.x),
                                coords=coords,
                                name=self.name)
        
        return xr.DataArray(self.data,
                            coords=coords,
                            name=self.name,
                            attrs=self.attrs)
    
    def __eq__(self, other: Any) -> bool:
        
        if not isinstance(other, Transect):
            return NotImplemented
        
        if not self.z == other.z: return False
        if not np.isclose(self.x, other.x).all(): return False
        if not np.isclose(self.y, other.y).all(): return False
        
        none_check = sum([1 if x is None else 0 for x in
                                                  [self.data, other.data]])
        
        if none_check == 1: return False
        
        if none_check == 0:
            assert self.data is not None
            assert other.data is not None
            if not np.isclose(self.data, other.data).all(): return False
        
        optionals = ("name", "attrs")
        
        for key in optionals:
            
            none_check = sum([1 if x is None else 0 for x in (self[key],
                                                              other[key])])
            
            if none_check == 1: return False
            if none_check == 0 and self[key] != other[key]: return False
        
        return True
    
    def __getitem__(self, item: str) -> Union[None,
                                              Num,
                                              npt.NDArray[np.float64]]:
        return getattr(self, item)


def get_normalised_dims(da: xr.DataArray, factor: Num) -> xr.DataArray:
    
    zstar = da["$z$"].values * factor
    xstar = da["$x$"].values * factor
    ystar = da["$y$"].values * factor
    
    new_da = da.assign_coords({"$z$": zstar,
                               "$x$": ("dim_0", xstar),
                               "$y$": ("dim_0", ystar)})
    
    new_da = new_da.rename({"$z$": "$z^*$",
                            "$x$": "$x^*$",
                            "$y$": "$y^*$"})
    
    return new_da


def get_normalised_data(da: xr.DataArray, factor: Num) -> xr.DataArray:
    
    datastar = da.values * factor
    name = str(da.name)
    
    if name is not None:
        
        name_dollars = name.count("$")
        
        if name_dollars > 0 and (name_dollars % 2) == 0:
            last_dollar = name.rfind("$")
            name = name[:last_dollar] + "^*" + name[last_dollar:]
        else:
            name = name + " *"
    
    return xr.DataArray(datastar,
                        coords=da.coords,
                        name=name,
                        attrs=da.attrs)


def get_normalised_data_deficit(da: xr.DataArray,
                                factor: Num,
                                name: Optional[str] = None) -> xr.DataArray:
    
    data = 100 * (1 - da.values / factor)
    
    return xr.DataArray(data,
                        coords=da.coords,
                        name=name,
                        attrs=da.attrs)
