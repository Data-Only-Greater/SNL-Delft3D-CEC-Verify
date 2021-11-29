# -*- coding: utf-8 -*-

import os
import collections
from typing import Dict, Optional, Sequence, Union
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from shapely.geometry import LineString

from .types import Num, StrOrPath


class Result:
    
    def __init__(self, project_path: StrOrPath):
        self.map: xr.Dataset = load_map(project_path)


def load_map(project_path: StrOrPath) -> xr.Dataset:
    map_path = Path(project_path) / "output" / "FlowFM_map.nc"
    return xr.load_dataset(map_path)


@dataclass
class Faces:
    map_path: StrOrPath
    _t_steps: Dict[int, pd.Timestamp] = field(default_factory=dict,
                                              init=False,
                                              repr=False)
    _frame: Optional[pd.DataFrame] = field(default=None,
                                           init=False,
                                           repr=False)
    
    def _extract(foo):
        
        def magic(self, t_step: int,
                        kz: Union[int, Num],
                        x: Optional[Sequence[Num]] = None,
                        y: Optional[Sequence[Num]] = None) -> xr.Dataset:
            
            do_interp = sum((bool(x is not None),
                             bool(y is not None)))
            
            if do_interp == 1:
                raise RuntimeError("x and y must both be set")
            
            if t_step not in self._t_steps:
                self._load_t_step(t_step)
            
            ds = foo(self, t_step, kz)
            
            if not do_interp: return ds
            
            x = xr.DataArray(x)
            y = xr.DataArray(y)
            
            return ds.interp(x=x, y=y)
            
        return magic
    
    @_extract
    def extract_z(self, t_step: int,
                        z: Num) -> xr.Dataset:
        return dataframe_to_dataset(self._frame,
                                    self._t_steps[t_step],
                                    z=z)
    
    @_extract
    def extract_k(self, t_step: int,
                        k: int) -> xr.Dataset:
        return dataframe_to_dataset(self._frame,
                                    self._t_steps[t_step],
                                    k=k)
    
    def _load_t_step(self, t_step: int):
        
        frame = map_to_dataframe(self.map_path, t_step)
        
        if self._frame is None:
            self._frame = frame
        else:
            self._frame = self._frame.append(frame,
                                             ignore_index=True,
                                             sort=False)
        
        self._t_steps[t_step] = pd.Timestamp(frame["time"].unique().take(0))


def map_to_dataframe(map_path: StrOrPath,
                     t_step: int = None) -> pd.DataFrame:
    
    data = collections.defaultdict(list)
    
    with xr.open_dataset(map_path) as ds:
        
        for iface in ds.mesh2d_nFaces.values:
            for k, ilayer in enumerate(ds.mesh2d_nLayers.values):
                
                data["x"].append(ds.mesh2d_face_x[iface].values.take(0))
                data["y"].append(ds.mesh2d_face_y[iface].values.take(0))
                data["z"].append(
                        ds.mesh2d_layer_sigma[ilayer].values * \
                                ds.mesh2d_waterdepth[t_step, iface].values)
                
                data["k"].append(k)
                data["time"].append(ds.time[t_step].values.take(0))
                
                data["u"].append(
                    ds.mesh2d_ucx[t_step, iface, ilayer].values.take(0))
                data["v"].append(
                    ds.mesh2d_ucy[t_step, iface, ilayer].values.take(0))
                data["w"].append(
                    ds.mesh2d_ucz[t_step, iface, ilayer].values.take(0))
    
    return pd.DataFrame(data)


def dataframe_to_dataset(frame: pd.DataFrame,
                         sim_time: pd.Timestamp,
                         k: Optional[int] = None,
                         z: Optional[Num] = None) -> xr.Dataset:
    
    if (k is None and z is None) or (k is not None and z is not None):
        raise RuntimeError("either k or z must be given")
    
    frame = frame.set_index(['x', 'y', 'z', 'time'])
    frame = frame.xs(sim_time, level=3)
    
    if z is None:
        
        kframe = frame[frame["k"] == k]
        kframe = kframe.drop("k", axis=1)
        kframe = kframe.reset_index(2)
        ds = kframe.to_xarray()
        ds = ds.assign_coords({"k": k})
    
    else:
        
        data = collections.defaultdict(list)
        
        for (x, y), group in frame.groupby(level=[0,1]):
            
            gframe = group.droplevel([0,1])
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
    
    return ds


def get_cell_data(ds, t=-1):
    
    points = []
    v = []
    
    for iface in ds.mesh2d_nFaces.values:
        
        x = ds.mesh2d_face_x[iface].values.take(0)
        y = ds.mesh2d_face_y[iface].values.take(0)
        
        for ilayer in ds.mesh2d_nLayers.values:
            
            z = ds.mesh2d_layer_sigma[ilayer].values * \
                                    ds.mesh2d_waterdepth[t, iface].values
            points.append([x, y, z])
            v.append(ds.mesh2d_ucx[t, iface, ilayer].values.take(0))
    
    np_points = np.array(points)
    np_v = np.array(v)
    
    return np_points, np_v



def get_edge_lines(ds):
    
    lines = []
    
    for iedge in ds.mesh2d_nEdges.values:
        
        points = []
        
        for inode in [0, 1]:
            
            x = ds.mesh2d_node_x[ds.mesh2d_edge_nodes[iedge, inode] - 1]
            y = ds.mesh2d_node_y[ds.mesh2d_edge_nodes[iedge, inode] - 1]
            
            points.append((x, y))
        
        lines.append(LineString(points))
        
    return lines


def plot_result(project_path, project_name):
    
    msg_str = ("***\n"
               "*** Post-processing model...\n"
               "***")
    print(msg_str)
    
    project_data_dir = "{}.dsproj_data".format(project_name)
    
    map_file = os.path.join(project_path,
                            project_data_dir,
                            "FlowFM",
                            "input",
                            "DFM_OUTPUT_FlowFM",
                            "FlowFM_map.nc")
    ds = xr.open_dataset(map_file)
    
    lines = get_edge_lines(ds)
    centerline = LineString([(0, 3), (18, 3)])
    mid_layer = len(ds.mesh2d_nLayers) // 2
    u1 = get_u1_intersection(ds, lines, centerline, layer=mid_layer)
    plot_intersect_x(u1, project_path, mid_layer)
    
    return



def get_u1_intersection(ds, lines, transect, t=-1, layer=8):
    
    data = []
    
    for i, line in enumerate(lines):
        
        if not line.intersects(transect) or is_parallel(transect, line):
            continue
            
        x = ds.mesh2d_edge_x[i].values.take(0)
        y = ds.mesh2d_edge_x[i].values.take(0)
        u1 = ds.mesh2d_u1[t, i, layer].values.take(0)
        
        data.append((x, y, u1))
    
    dtype = [('x', 'float'), ('y', 'float'), ('value', 'float')]
    out = np.array(data, dtype=dtype)
    out.sort(order=["x", "y"])
    
    return out


def is_parallel(a, b, tol=1e-9):
    
    result = False
    
    a_vec = np.array((a.coords[1][0] - a.coords[0][0],
                      a.coords[1][1] - a.coords[0][1]))
    b_vec = np.array((b.coords[1][0] - b.coords[0][0],
                      b.coords[1][1] - b.coords[0][1]))
        
    axb = np.cross(a_vec, b_vec)
    if abs(axb) < tol: result = True
        
    return result


def plot_intersect_x(u1, project_path, layer):
    
    fig_path = os.path.join(project_path, "centerline_edge_u1.png")
    
    plt.figure(figsize=(10,4))
    plt.plot(u1["x"], u1["value"])
    plt.axvline(6, color='k', ls="dashed")
    plt.text(6.2,-0.5,'turbine',rotation=90)
    plt.ylabel("u1 (m/s)")
    plt.xlabel("x (m)")
    title_str = ("Edge velocities intersecting turbine centerline (layer "
                 "{})").format(layer)
    plt.title(title_str)
    plt.savefig(fig_path, bbox_inches='tight')
    
    msg_str = ("*** Plot created at '{}'\n"
               "***").format(fig_path)
    print(msg_str)
    
    return
