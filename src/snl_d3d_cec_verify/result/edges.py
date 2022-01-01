# -*- coding: utf-8 -*-

from __future__ import annotations

import collections
from typing import Dict, Optional
from dataclasses import dataclass, field

import numpy as np
import pandas as pd # type: ignore
import geopandas as gpd # type: ignore
import xarray as xr
from shapely.geometry import LineString # type: ignore
from shapely.geometry.base import BaseGeometry # type: ignore

from .base import TimeStepResolver
from ..types import StrOrPath


@dataclass
class Edges(TimeStepResolver):
    _t_steps: Dict[int, pd.Timestamp] = field(default_factory=dict,
                                              init=False,
                                              repr=False)
    _frame: Optional[gpd.GeoDataFrame] = field(default=None,
                                               init=False,
                                               repr=False)
    
    def extract_k(self, t_step: int,
                        k: int,
                        goem: Optional[BaseGeometry] = None
                                                    ) -> gpd.GeoDataFrame:
        
        t_step = self._resolve_t_step(t_step)
        
        if t_step not in self._t_steps:
            self._load_t_step(t_step)
        
        assert self._frame is not None
        
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
        
        return gframe.reset_index(drop=True)
    
    def _load_t_step(self, t_step: int):
        
        t_step = self._resolve_t_step(t_step)
        if t_step in self._t_steps: return
        
        frame = _map_to_edges_geoframe(self.map_path, t_step)
        
        if self._frame is None:
            self._frame = frame
        else:
            self._frame = self._frame.append(frame,
                                             ignore_index=True,
                                             sort=False)
        
        self._t_steps[t_step] = pd.Timestamp(frame["time"].unique().take(0))


def _map_to_edges_geoframe(map_path: StrOrPath,
                          t_step: int = None) -> gpd.GeoDataFrame:
    
    data = collections.defaultdict(list)
    
    with xr.open_dataset(map_path) as ds:
    
        time = ds.time[t_step].values.take(0)
        
        for iedge in ds.mesh2d_nEdges.values:
            
            points = []
            two = (0, 1)
            
            for inode in two:
                index = ds.mesh2d_edge_nodes[iedge, inode] - 1
                x = ds.mesh2d_node_x[index]
                y = ds.mesh2d_node_y[index]
                p = np.array((x, y))
                points.append(p)
            
            line = LineString(points)
            linevec = points[1] - points[0]
            normvec = np.array((-linevec[1], linevec[0]))
            
            points = []
            
            for iface in two:
                
                index = int(ds.mesh2d_edge_faces[iedge, iface]) - 1
                
                if index < 0:
                    p = np.array(line.centroid)
                else:
                    x = ds.mesh2d_face_x[index]
                    y = ds.mesh2d_face_y[index]
                    p = np.array((x, y))
                
                points.append(p)
            
            facevec = points[1] - points[0]
            normvec *= np.dot(facevec, normvec)
            normvec /= np.linalg.norm(normvec)
            
            for k, ilayer in enumerate(ds.mesh2d_nLayers.values):
                
                u1 = ds.mesh2d_u1[t_step, iedge, ilayer].values.take(0)
                
                data["geometry"].append(line)
                data["k"].append(k)
                data["time"].append(time)
                data["u1"].append(u1)
                data["n0"].append(normvec[0])
                data["n1"].append(normvec[1])
    
    return gpd.GeoDataFrame(data)
