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

from .base import _TimeStepResolver
from ..types import StrOrPath


@dataclass
class Edges(_TimeStepResolver):
    """Class for extracting results on the edges of the simulation grid for 
    flexible mesh (``'fm'``) models. Use in conjunction with the 
    :class:`.Result` class.
    
    >>> from snl_d3d_cec_verify import Result
    >>> data_dir = getfixture('data_dir')
    >>> result = Result(data_dir)
    >>> result.edges.extract_k(-1, 1) #doctest: +ELLIPSIS
                                            geometry            u1   n0   n1
    0      LINESTRING (1.00000 2.00000, 0.00000 2.00000) -3.662849e-17  0.0  1.0
    ...
    
    :param nc_path: path to the ``.nc`` file containing results
    :param n_steps: number of time steps in the simulation
    
    """
    
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
        """Extract data from the grid edges for a given time step and sigma
        level (:code:`k`). Available data is:
        
        * :code:`u1`: velocity, in metres per second
        * :code:`n0`: edge normal x-coordinate
        * :code:`n1`: edge normal y-coordinate
        
        Results are returned as a :class:`geopandas.GeoDataFrame`, either 
        for all of the edges or for the result of the intersection with 
        :code:`geom` if set. For example:
        
        >>> from shapely.geometry import LineString
        >>> from snl_d3d_cec_verify import Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> line = LineString([(6, 2), (10, 2)])
        >>> result.edges.extract_k(-1, 1, line)
                   geometry            u1
        0   POINT (6.00000 2.00000) -6.794595e-18
        1   POINT (7.00000 2.00000)  7.732358e-01
        2   POINT (8.00000 2.00000)  7.753754e-01
        3   POINT (9.00000 2.00000)  7.737631e-01
        4  POINT (10.00000 2.00000)  7.750168e-01
        
        :param t_step: Time step index
        :param k: sigma level
        :param goem: Optional shapely geometry, where data is extracted on
            the intersection with the grid edges using the 
            :meth:`object.intersection` method.
        
        :raises IndexError: if the time-step index (``t_step``) is
            out of range
        
        :return: Returns a :class:`geopandas.GeoDataFrame` with 
            :class:`LineString` geometries for each edge or the result of the
            intersection with :code:`geom` if set.
        
        """
        
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
        
        frame = _map_to_edges_geoframe(self.nc_path, t_step)
        
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
        edge_node_values = ds.mesh2d_edge_nodes.values
        edge_face_values = ds.mesh2d_edge_faces.values
        node_x_values = ds.mesh2d_node_x.values
        node_y_values = ds.mesh2d_node_y.values
        face_x_values = ds.mesh2d_face_x.values
        face_y_values = ds.mesh2d_face_y.values
        u1_values = ds.mesh2d_u1.values
        
        for iedge in ds.mesh2d_nEdges.values:
            
            points = []
            two = (0, 1)
            
            for inode in two:
                index = edge_node_values[iedge, inode] - 1
                x = node_x_values[index]
                y = node_y_values[index]
                p = np.array((x, y))
                points.append(p)
            
            line = LineString(points)
            linevec = points[1] - points[0]
            normvec = np.array((-linevec[1], linevec[0]))
            
            points = []
            
            for iface in two:
                
                index = int(edge_face_values[iedge, iface]) - 1
                
                if index < 0:
                    p = np.array(line.centroid)
                else:
                    x = face_x_values[index]
                    y = face_y_values[index]
                    p = np.array((x, y))
                
                points.append(p)
            
            facevec = points[1] - points[0]
            normvec *= np.dot(facevec, normvec)
            normvec /= np.linalg.norm(normvec)
            
            for k, ilayer in enumerate(ds.mesh2d_nLayers.values):
                
                u1 = u1_values[t_step, iedge, ilayer]
                
                data["geometry"].append(line)
                data["k"].append(k)
                data["time"].append(time)
                data["u1"].append(u1)
                data["n0"].append(normvec[0])
                data["n1"].append(normvec[1])
    
    return gpd.GeoDataFrame(data)
