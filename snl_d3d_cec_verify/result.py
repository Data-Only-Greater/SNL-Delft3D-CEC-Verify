# -*- coding: utf-8 -*-

import os
import collections
from typing import Optional, Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from shapely.geometry import LineString

from .types import StrOrPath


class Result:
    
    def __init__(self, project_path: StrOrPath):
        self.map: xr.Dataset = load_map(project_path)


class Interp:
    
    def __init__(self):
        
        self.points = {}
        self.values = {}

    def get_cell_data(self, ds, t=-1):
        
        time = ds.time[t].values
        
        if time in self.points:
            return self.points[time].copy(), self.values[time].copy()

        points = []
        v = []

        for iface in ds.mesh2d_nFaces.values:

            x = ds.mesh2d_face_x[iface].values.take(0)
            y = ds.mesh2d_face_y[iface].values.take(0)

            for ilayer in ds.mesh2d_nLayers.values:

                z = ds.mesh2d_layer_sigma[ilayer].values * ds.mesh2d_waterdepth[t, iface].values
                points.append([x, y, z])
                v.append(ds.mesh2d_ucx[t, iface, ilayer].values.take(0))

        np_points = np.array(points)
        np_v = np.array(v)
        
        self.points[time] = np_points.copy()
        self.values[time] = np_v.copy()

        return np_points, np_v

    def get_turb_v(self, ds, x, y, t=-1, ldimension=None, x0=None, y0=None, vdimension=None, method='linear'):

        x = np.array(x, copy=True).astype(float)
        y = np.array(y, copy=True).astype(float)

        if ldimension is not None:
            x *= ldimension
            y *= ldimension

        if x0 is not None: x += x0
        if y0 is not None: y += y0

        points, values = self.get_cell_data(ds, t)
        X, Y, Z = np.meshgrid(x, y, -1)
        V = griddata(points, values, (X.flatten(),Y.flatten(),Z.flatten()), method=method)

        if vdimension is not None: V /= vdimension

        return V

    def transect_2norm_error(self, ds, df, t=-1):

        y = df["y*"].copy()
        v = self.get_turb_v(ds, 5, y, ldimension=0.7, x0=6, y0=3, vdimension=0.8, t=t)
        error = np.linalg.norm(v - df["ubar*"]) / np.linalg.norm(df["ubar*"])

        return error
    
    def __getstate__(self):
        
        basic_points = {str(time): np_points.tolist() for time, np_points in self.points.items()}
        basic_values = {str(time): np_values.tolist() for time, np_values in self.values.items()}
        d = {"points": basic_points,
             "values": basic_values}
        
        return d
    
    def __setstate__(self, d):
        
        np_points = {np.datetime64(time): np.array(basic_points) for time, basic_points in d["points"].items()}
        np_values = {np.datetime64(time): np.array(basic_values) for time, basic_values in d["values"].items()}
        
        self.points = np_points
        self.values = np_values
        
        return



def load_map(project_path: StrOrPath) -> xr.Dataset:
    map_path = Path(project_path) / "output" / "FlowFM_map.nc"
    return xr.load_dataset(map_path)


def map_to_grid(map_path: StrOrPath,
                t_steps: Optional[Sequence[int]] = None):
    
    if t_steps is None:
        t_steps = [-1]
    
    data = collections.defaultdict(list)
    
    with xr.open_dataset(map_path) as ds:
        
        for t_step in t_steps:
            for iface in ds.mesh2d_nFaces.values:
                for k, ilayer in enumerate(ds.mesh2d_nLayers.values):
                    
                    data["x"].append(ds.mesh2d_face_x[iface].values.take(0))
                    data["y"].append(ds.mesh2d_face_y[iface].values.take(0))
                    data["k"].append(k)
                    data["time"].append(ds.time[t_step].values.take(0))
                    
                    data["z"].append(
                        ds.mesh2d_layer_sigma[ilayer].values * \
                                ds.mesh2d_waterdepth[t_step, iface].values)
                    data["u"].append(
                        ds.mesh2d_ucx[t_step, iface, ilayer].values.take(0))
                    data["v"].append(
                        ds.mesh2d_ucy[t_step, iface, ilayer].values.take(0))
                    data["w"].append(
                        ds.mesh2d_ucz[t_step, iface, ilayer].values.take(0))
    
    df = pd.DataFrame(data)
    df = df.set_index(['x', 'y', 'k', 'time'])
    
    return df


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


def get_turb_v(ds, method='linear', t=-1):
    
    points, values = get_cell_data(ds, t)
    X, Y, Z = np.meshgrid(6, 3, -1)
    V = griddata(points,
                 values,
                 (X.flatten(),Y.flatten(),Z.flatten()),
                 method=method)
    
    return V[0]


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
