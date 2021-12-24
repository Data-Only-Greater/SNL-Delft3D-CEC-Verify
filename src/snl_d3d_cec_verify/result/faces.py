# -*- coding: utf-8 -*-

from __future__ import annotations

import collections
from typing import (cast,
                    Dict,
                    Optional,
                    Sequence,
                    TYPE_CHECKING)
from dataclasses import dataclass, field

import numpy as np
import pandas as pd # type: ignore
import xarray as xr

from .base import TimeStepResolver
from ..types import Num, StrOrPath

if TYPE_CHECKING: # pragma: no cover
    from ..cases import CaseStudy


# TODO: I'd like to type check this, but I can't get it to work.
def _extract(method):
    
    def magic(self, t_step: int,
                    kz: Num,
                    x: Optional[Sequence[Num]] = None,
                    y: Optional[Sequence[Num]] = None) -> xr.Dataset:
        
        do_interp = sum((bool(x is not None),
                         bool(y is not None)))
        
        if do_interp == 1:
            raise RuntimeError("x and y must both be set")
        
        t_step = self.resolve_t_step(t_step)
        
        if t_step not in self._t_steps:
            self._load_t_step(t_step)
        
        ds = method(self, t_step, kz)
        
        if not do_interp: return ds
        
        return ds.interp({"$x$": xr.DataArray(x),
                          "$y$": xr.DataArray(y)})
        
    return magic


@dataclass
class Faces(TimeStepResolver):
    xmax: Num
    _t_steps: Dict[int, pd.Timestamp] = field(default_factory=dict,
                                              init=False,
                                              repr=False)
    _frame: Optional[pd.DataFrame] = field(default=None,
                                           init=False,
                                           repr=False)
    
    def extract_turbine_centre(self, t_step: int,
                                     case: CaseStudy,
                                     offset_x: Num = 0,
                                     offset_y: Num = 0,
                                     offset_z: Num = 0) -> xr.Dataset:
        
        _check_case_study(case)
        
        # Inform the type checker that we have Num for single value cases
        turb_pos_z = cast(Num, case.turb_pos_z)
        turb_pos_x = cast(Num, case.turb_pos_x)
        turb_pos_y = cast(Num, case.turb_pos_y)
        
        return self.extract_z(t_step,
                              turb_pos_z + offset_z,
                              [turb_pos_x + offset_x],
                              [turb_pos_y + offset_y])
    
    def extract_turbine_centreline(self, t_step: int,
                                         case: CaseStudy,
                                         x_step: Num = 0.5,
                                         offset_x: Num = 0,
                                         offset_y: Num = 0,
                                         offset_z: Num = 0) -> xr.Dataset:
        
        _check_case_study(case)
        
        # Inform the type checker that we have Num for single value cases
        turb_pos_z = cast(Num, case.turb_pos_z)
        turb_pos_x = cast(Num, case.turb_pos_x)
        turb_pos_y = cast(Num, case.turb_pos_y)
        
        x = np.arange(turb_pos_x + offset_x, self.xmax, x_step)
        if np.isclose(x[-1] + x_step, self.xmax): x = np.append(x, self.xmax)
        y = [turb_pos_y + offset_y] * len(x)
        
        return self.extract_z(t_step, turb_pos_z + offset_z, x, y)
    
    def extract_turbine_z(self, t_step: int,
                                case: CaseStudy,
                                offset_z: Num = 0) -> xr.Dataset:
        
        _check_case_study(case)
        turb_pos_z = cast(Num, case.turb_pos_z)
        
        return self.extract_z(t_step, turb_pos_z + offset_z)
    
    @_extract
    def extract_z(self, t_step: int,
                        z: Num) -> xr.Dataset:
        return faces_frame_to_slice(self._frame,
                                    self._t_steps[t_step],
                                    z=z)
    
    @_extract
    def extract_k(self, t_step: int,
                        k: int) -> xr.Dataset:
        return faces_frame_to_slice(self._frame,
                                    self._t_steps[t_step],
                                    k=k)
    
    def extract_depth(self, t_step: int) -> xr.DataArray:
        
        t_step = self.resolve_t_step(t_step)
        
        if t_step not in self._t_steps:
            self._load_t_step(t_step)
        
        return faces_frame_to_depth(self._frame,
                                    self._t_steps[t_step])
    
    def _load_t_step(self, t_step: int):
        
        t_step = self.resolve_t_step(t_step)
        if t_step in self._t_steps: return
        
        frame = map_to_faces_frame(self.map_path, t_step)
        
        if self._frame is None:
            self._frame = frame
        else:
            self._frame = self._frame.append(frame,
                                             ignore_index=True,
                                             sort=False)
        
        self._t_steps[t_step] = pd.Timestamp(frame["time"].unique().take(0))


def _check_case_study(case: CaseStudy):
    if len(case) != 1:
        raise ValueError("case study must have length one")


def map_to_faces_frame(map_path: StrOrPath,
                       t_step: int = None) -> pd.DataFrame:
    
    data = collections.defaultdict(list)
    
    with xr.open_dataset(map_path) as ds:
        
        time = ds.time[t_step].values.take(0)
        
        for iface in ds.mesh2d_nFaces.values:
            
            x = ds.mesh2d_face_x[iface].values.take(0)
            y = ds.mesh2d_face_y[iface].values.take(0)
            depth = ds.mesh2d_waterdepth[t_step, iface].values.take(0)
            
            for k, ilayer in enumerate(ds.mesh2d_nLayers.values):
                
                z = ds.mesh2d_layer_sigma[ilayer].values * \
                                ds.mesh2d_waterdepth[t_step, iface].values
                u = ds.mesh2d_ucx[t_step, iface, ilayer].values.take(0)
                v = ds.mesh2d_ucy[t_step, iface, ilayer].values.take(0)
                w = ds.mesh2d_ucz[t_step, iface, ilayer].values.take(0)
                
                data["x"].append(x)
                data["y"].append(y)
                data["z"].append(z)
                data["k"].append(k)
                data["time"].append(time)
                data["depth"].append(depth)
                data["u"].append(u)
                data["v"].append(v)
                data["w"].append(w)
    
    return pd.DataFrame(data)


def faces_frame_to_slice(frame: pd.DataFrame,
                         sim_time: pd.Timestamp,
                         k: Optional[int] = None,
                         z: Optional[Num] = None) -> xr.Dataset:
    
    if (k is None and z is None) or (k is not None and z is not None):
        raise RuntimeError("either k or z must be given")
    
    frame = frame.set_index(['x', 'y', 'z', 'time'])
    frame = frame.xs(sim_time, level=3)
    
    if z is None:
        
        kframe = frame[frame["k"] == k]
        kframe = kframe.drop(["depth", "k"], axis=1)
        kframe = kframe.reset_index(2)
        ds = kframe.to_xarray()
        ds = ds.assign_coords({"k": k})
    
    else:
        
        data = collections.defaultdict(list)
        
        for (x, y), group in frame.groupby(level=[0, 1]):
            
            gframe = group.droplevel([0, 1])
            zvalues = gframe.reindex(
                        gframe.index.union([z])).interpolate('values').loc[z]
            
            data["x"].append(x)
            data["y"].append(y)
            data["k"].append(zvalues["k"])
            data["u"].append(zvalues["u"])
            data["v"].append(zvalues["v"])
            data["w"].append(zvalues["w"])
            
        zframe = pd.DataFrame(data)
        zframe = zframe.set_index(['x', 'y'])
        ds = zframe.to_xarray()
        ds = ds.assign_coords({"z": z})
    
    ds = ds.assign_coords({"time": sim_time})
    ds = ds.rename({"z": "$z$",
                    "x": "$x$",
                    "y": "$y$",
                    "u": "$u$",
                    "v": "$v$",
                    "w": "$w$"})
    
    return ds


def faces_frame_to_depth(frame: pd.DataFrame,
                         sim_time: pd.Timestamp) -> xr.DataArray:
    
    frame = frame.set_index(['x', 'y', 'k', 'time'])
    frame = frame.xs((0, sim_time), level=(2, 3))
    frame = frame.drop(["z", "u", "v", "w"], axis=1)
    ds = frame.to_xarray()
    ds = ds.assign_coords({"time": sim_time})
    
    return ds.depth
