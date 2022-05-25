# -*- coding: utf-8 -*-

from __future__ import annotations

import warnings
import collections
from typing import Dict, Optional
from dataclasses import dataclass, field

import numpy as np
import pandas as pd # type: ignore
import xarray as xr
from shapely.geometry import LineString # type: ignore
from shapely.geometry.base import BaseGeometry # type: ignore

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import geopandas as gpd # type: ignore

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
    >>> result.edges.extract_sigma(-1, 0.5) #doctest: +ELLIPSIS
                                               geometry            u1  ...   n0   n1
    0     LINESTRING (0.00000 1.00000, 0.00000 2.00000)  9.753143e-01  ...  1.0 -0.0
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
    
    def extract_sigma(self, t_step: int,
                            value: float,
                            goem: Optional[BaseGeometry] = None
                            ) -> gpd.GeoDataFrame:
        """Extract data from the grid edges for a given time step and sigma
        level (:code:`sigma`). Available data is:
        
        * :code:`u1`: velocity, in metres per second
        * :code:`k`: turbulent kinetic energy, in metres squared per second
          squared
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
        >>> result.edges.extract_sigma(-1, 0.5, line)
                           geometry        u1       $k$
        0  POINT (10.00000 2.00000)  0.991826 -0.004130
        1   POINT (6.00000 2.00000)  0.991709 -0.004194
        2   POINT (7.00000 2.00000)  0.974911 -0.004177
        3   POINT (8.00000 2.00000)  0.992091 -0.004168
        4   POINT (9.00000 2.00000)  0.976797 -0.004141
        
        :param t_step: Time step index
        :param sigma: sigma level
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
        
        gdf = self._frame.copy()
        gdf['wkt'] = gdf['geometry'].apply(lambda geom: geom.wkt)
        
        gdf = gdf.set_index(['wkt', 'time'])
        gdf = gdf.xs(self._t_steps[t_step], level=1)
        
        data = collections.defaultdict(list)
        
        for _, group in gdf.groupby(by="wkt"):
            
            geometry = group["geometry"].values[0]
            n0 = group["n0"].values[0]
            n1 = group["n1"].values[0]
            gframe = group.set_index("sigma")
            gframe = gframe.drop("geometry", axis=1)
            df = pd.DataFrame(gframe)
            
            svalues = df.reindex(df.index.union([value])
                            ).interpolate('slinear',
                                          fill_value="extrapolate",
                                          limit_direction="both").loc[value]
            
            data["geometry"].append(geometry)
            data["u1"].append(svalues["u1"])
            data["$k$"].append(svalues["turkin1"])
            data["n0"].append(n0)
            data["n1"].append(n1)
        
        gframe = gpd.GeoDataFrame(data)
        
        if goem is None: return gframe
        
        pdata = {}
        pfilter = gframe.intersection(goem).geom_type == "Point"
        
        pdata["geometry"] = gframe.intersection(goem)[pfilter]
        pdata["u1"] = gframe[pfilter]["u1"]
        pdata["$k$"] = gframe[pfilter]["$k$"]
        
        gframe = gpd.GeoDataFrame(pdata)
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
            self._frame = pd.concat([self._frame, frame],
                                    ignore_index=True)
        
        self._t_steps[t_step] = pd.Timestamp(frame["time"].unique().take(0))


def _map_to_edges_geoframe(map_path: StrOrPath,
                          t_step: int = None) -> gpd.GeoDataFrame:
    
    data = collections.defaultdict(list)
    
    with xr.open_dataset(map_path) as ds:
        
        if t_step is None:
            t_steps = tuple(range(len(ds.time)))
        else:
            t_steps = (t_step,)
        
        for istep in t_steps:
            
            time = ds.time[istep].values.take(0)
            edge_node_values = ds.mesh2d_edge_nodes.values
            edge_face_values = ds.mesh2d_edge_faces.values
            node_x_values = ds.mesh2d_node_x.values
            node_y_values = ds.mesh2d_node_y.values
            face_x_values = ds.mesh2d_face_x.values
            face_y_values = ds.mesh2d_face_y.values
            layer_sigma_values = ds.mesh2d_layer_sigma.values
            interface_sigma_values = ds.mesh2d_interface_sigma.values
            u1_values = ds.mesh2d_u1.values
            tke_values = ds.mesh2d_turkin1.values
            
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
                        p = np.array(line.centroid.coords)
                    else:
                        x = face_x_values[index]
                        y = face_y_values[index]
                        p = np.array((x, y))
                    
                    points.append(p)
                
                facevec = points[1] - points[0]
                normvec *= np.dot(facevec, normvec)
                normvec /= np.linalg.norm(normvec)
                tke = np.nan
                
                for ilayer in ds.mesh2d_nLayers.values:
                    
                    sigma = layer_sigma_values[ilayer]
                    u1 = u1_values[istep, iedge, ilayer]
                    
                    data["geometry"].append(line)
                    data["sigma"].append(sigma)
                    data["time"].append(time)
                    data["u1"].append(u1)
                    data["turkin1"].append(tke)
                    data["n0"].append(normvec[0])
                    data["n1"].append(normvec[1])
                
                u1 = np.nan
                
                for iinterface in ds.mesh2d_nInterfaces.values:
                    
                    sigma = interface_sigma_values[iinterface]
                    tke = tke_values[istep, iedge, iinterface]
                    
                    data["geometry"].append(line)
                    data["sigma"].append(sigma)
                    data["time"].append(time)
                    data["u1"].append(u1)
                    data["turkin1"].append(tke)
                    data["n0"].append(normvec[0])
                    data["n1"].append(normvec[1])
    
    gdf = gpd.GeoDataFrame(data)
    gdf['wkt'] = gdf['geometry'].apply(lambda geom: geom.wkt)
    gdf = gdf.set_index(['wkt', 'time', 'sigma'])
    gdf = gdf.sort_index()
    new_gdf = gpd.GeoDataFrame()
    
    for (_, time), group in gdf.groupby(level=[0, 1]):
        
        group = group.reset_index(["wkt", "time"], drop=True)
        geometry = group["geometry"].unique()[0]
        group = group.drop("geometry", axis=1)
        
        df = pd.DataFrame(group)
        df = df.interpolate('slinear',
                            fill_value="extrapolate",
                            limit_direction="both")
        
        group = gpd.GeoDataFrame(df)
        group["geometry"] = geometry
        group["time"] = time
        group = group.reset_index()
        
        new_gdf = pd.concat([new_gdf, group])
    
    new_gdf = new_gdf.reset_index(drop=True)
    
    return new_gdf[["geometry",
                    "sigma",
                    "time",
                    "u1",
                    "turkin1",
                    "n0",
                    "n1"]]
