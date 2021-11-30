# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import collections
from typing import Dict, Optional, Sequence, Tuple, TYPE_CHECKING, Union
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import matplotlib.pyplot as plt
from shapely.geometry import LineString

from ..types import Num, StrOrPath

if TYPE_CHECKING:
    from ..cases import CaseStudy
    from shapely.geometry.base import BaseGeometry


@dataclass
class Edges:
    map_path: StrOrPath
    _t_steps: Dict[int, pd.Timestamp] = field(default_factory=dict,
                                              init=False,
                                              repr=False)
    _frame: Optional[pd.DataFrame] = field(default=None,
                                           init=False,
                                           repr=False)
    
    def extract_k(self, t_step: int,
                        k: int,
                        goem: Optional[BaseGeometry] = None
                                                    ) -> gpd.GeoDataFrame:
        
        if t_step not in self._t_steps:
            self._load_t_step(t_step)
        
        kframe = self._frame.set_index(['time', 'k'])
        kframe = kframe.sort_index()
        kframe = kframe.loc[(self._t_steps[t_step], k)]
        kframe = kframe.reset_index(drop=True)
        
        if goem is None: return kframe
        
        data = {}
        pfilter = kframe.intersection(goem).geom_type == "Point"
        
        data["geometry"] = kframe.intersection(goem)[pfilter]
        data["u1"] = kframe[pfilter]["u1"]
        
        gframe = gpd.GeoDataFrame(data)
        gframe["wkt"] = gframe["geometry"].apply(lambda geom: geom.wkt)
        gframe = gframe.drop_duplicates(["wkt"])
        gframe = gframe.drop("wkt", axis=1)
        
        return gframe
    
    def _load_t_step(self, t_step: int):
    
        frame = map_to_edges_geoframe(self.map_path, t_step)
        
        if self._frame is None:
            self._frame = frame
        else:
            self._frame = self._frame.append(frame,
                                             ignore_index=True,
                                             sort=False)
        self._t_steps[t_step] = pd.Timestamp(frame["time"].unique().take(0))


def map_to_edges_geoframe(map_path: StrOrPath,
                       t_step: int = None) -> pd.DataFrame:
    
    data = collections.defaultdict(list)
    
    with xr.open_dataset(map_path) as ds:
    
        time = ds.time[t_step].values.take(0)
        
        for iedge in ds.mesh2d_nEdges.values:
            
            points = []
            
            for inode in [0, 1]:
                index = ds.mesh2d_edge_nodes[iedge, inode] - 1
                x = ds.mesh2d_node_x[index]
                y = ds.mesh2d_node_y[index]
                points.append((x, y))
            
            line = LineString(points)
            
            for k, ilayer in enumerate(ds.mesh2d_nLayers.values):
                
                u1 = ds.mesh2d_u1[t_step, iedge, ilayer].values.take(0)
                
                data["geometry"].append(line)
                data["k"].append(k)
                data["time"].append(time)
                data["u1"].append(u1)
    
    return gpd.GeoDataFrame(data)


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
