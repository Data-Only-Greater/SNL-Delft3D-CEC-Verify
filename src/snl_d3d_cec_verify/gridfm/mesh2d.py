# -*- coding: utf-8 -*-

# Copyright (c) 2021, Mathew Topper
# Copyright (c) 2019, Guus Rongen

from __future__ import annotations

from ctypes import c_char, pointer
from typing import Optional, TYPE_CHECKING
from itertools import product
from collections import defaultdict

import numpy as np
import pandas as pd # type: ignore

from shapely.geometry import MultiPolygon, Polygon # type: ignore

from .checks import check_argument
from .cstructures import meshgeom, meshgeomdim
from .geometry import as_polygon_list
from ..types import Num

if TYPE_CHECKING: # pragma: no cover
    import numpy.typing as npt


class Mesh2D:

    def __init__(self):
        self.fill_value_z = -999.0
        self.missing_z_value = None
        
        self.meshgeomdim = meshgeomdim(pointer(c_char()),
                                       2,
                                       0,
                                       0,
                                       0,
                                       0,
                                       -1,
                                       -1,
                                       -1,
                                       -1,
                                       -1,
                                       0)
        self.meshgeom = meshgeom(self.meshgeomdim)
    
    def altitude_constant(self, constant, where='face'):
        zvalues = np.ones(getattr(self.meshgeomdim, f'num{where}')) * constant
        self.meshgeom.set_values(f'{where}z', zvalues)
    
    def set_missing_z_value(self, value):
        self.missing_z_value = value


class Rectangular(Mesh2D):
    
    def __init__(self):
        Mesh2D.__init__(self)
        self.meshgeomdim.maxnumfacenodes = 4
        self.rotated = False
        
    def generate_grid(self, x0,
                            y0,
                            xsize,
                            ysize,
                            dx,
                            dy):
        """
        Generate rectangular grid based on the origin (x0, y0) and size 
        (xsize, ysize) with the cell sizes (dx, dy). Last row and column
        will have size adjusted if dx and dy do not divide perfectly.
        """
        
        # Generate x and y spacing
        ncols = int(xsize / dx)
        nrows = int(ysize / dy)
        
        x1 = x0 + xsize
        y1 = y0 + ysize
        
        x = np.linspace(x0, x0 + dx * (ncols), ncols + 1)
        y = np.linspace(y0, y0 + dy * (nrows), nrows + 1)
        
        # Adjust last row and column if overlap
        if not np.isclose(x[-1], x1):
            x = np.append(x, x1) 
        
        if not np.isclose(y[-1], y1):
            y = np.append(y, y1)
        
        # Record spacing of last row and column
        c0 = x[-1] - x[-2]
        c1 = y[-1] - y[-2]
        
        # Get nodes
        xnodes, ynodes = np.meshgrid(x, y)
        
        # Get nodes as list
        nodes = {crd: i+1 for i, crd in enumerate(zip(xnodes.ravel(),
                                                      ynodes.ravel()))}
        
        # Get nodes as dataframe
        node_data = defaultdict(list)
        
        for (ix, iy), i in nodes.items():
            node_data["index"].append(i)
            node_data["x"].append(ix)
            node_data["y"].append(iy)
        
        node_df = pd.DataFrame(node_data)
        node_df = node_df.set_index("index")
        
        # Create segments
        segments = list(zip(
            zip(*np.c_[xnodes[:, :-1].ravel(), ynodes[:, :-1].ravel()].T),
            zip(*np.c_[xnodes[:, 1:].ravel(), ynodes[:, 1:].ravel()].T)))
        segments += list(zip(
            zip(*np.c_[xnodes[1:, :].ravel(), ynodes[1:, :].ravel()].T),
            zip(*np.c_[xnodes[:-1, :].ravel(), ynodes[:-1, :].ravel()].T)))
        
        # Get links
        edge_nodes = np.asarray([(nodes[s[0]], nodes[s[1]])
                                                         for s in segments])
        
        # Get face xy as a dataframe
        face_x = (x[:-1] + x[1:]) / 2
        face_y = (y[:-1] + y[1:]) / 2
        
        data = defaultdict(list)
        
        for i, (ix, iy) in enumerate(product(face_x, face_y)):
            data["index"].append(i + 1)
            data["x"].append(ix)
            data["y"].append(iy)
        
        face_df = pd.DataFrame(data)
        face_df = face_df.set_index("index")
        
        # Get the face nodes
        face_nodes =  np.asarray(
            [_get_face_nodes(node_df, row.values, dx, dy, x1, y1, c0, c1)
                                         for _, row in face_df.iterrows()])
        
        # Rvael the nodes and faces
        xnodes = xnodes.ravel()
        ynodes = ynodes.ravel()
        xfaces = face_df["x"].values.ravel()
        yfaces = face_df["y"].values.ravel()
        
        # Add to mesh
        dimensions = meshgeomdim()
        dimensions.dim = 2
        geometries = meshgeom(dimensions)
        
        # Update dimensions
        dimensions.numnode = len(xnodes)
        dimensions.numedge = len(edge_nodes)
        dimensions.numface = len(face_nodes)
        dimensions.maxnumfacenodes = 4
        
        # Add nodes, faces and links
        geometries.set_values('nodex', xnodes)
        geometries.set_values('nodey', ynodes)
        geometries.set_values('facex', xfaces)
        geometries.set_values('facey', yfaces)
        geometries.set_values('edge_nodes', np.ravel(edge_nodes).tolist())
        geometries.set_values('face_nodes', np.ravel(face_nodes).tolist())
        
        # Add to mesh
        self.meshgeom.add_from_other(geometries)
    
    def generate_within_polygon(self, polygon, dx, dy):
        """
        Function to generate a grid within a polygon. It uses the function
        'generate_grid' but automatically detects the extent.
        
        Parameters
        ----------
        polygon : (list of) shapely.geometry.Polygon or a
                  shapely.geometry.MultiPolygon
        """
        
        check_argument(polygon, 'polygon', (list, Polygon, MultiPolygon))
        polygons = as_polygon_list(polygon)
        convex = MultiPolygon(polygons).convex_hull
        
        xsize = convex.bounds[2] - convex.bounds[0]
        ysize = convex.bounds[3] - convex.bounds[1]
        x0, y0 = convex.bounds[0], convex.bounds[1]
        
        self.generate_grid(x0=x0,
                           y0=y0,
                           xsize=xsize,
                           ysize=ysize,
                           dx=dx,
                           dy=dy)


def _get_face_nodes(df: pd.DataFrame,
                    node: npt.NDArray[np.float64],
                    dx: Num,
                    dy: Num,
                    x1: Num,
                    y1: Num,
                    c0: float,
                    c1: float) -> npt.NDArray[np.int_]:
    
    shift_x = dx / 2
    shift_y = dy / 2
    
    half_c0 = c0 / 2
    half_c1 = c1 / 2
    
    # Edge cases
    if node[0] + shift_x > x1:
        shift_x = half_c0
    
    if node[1] + shift_y > y1:
        shift_y = half_c1
        
    search = [(-1 * shift_x, -1 * shift_y),
              (shift_x, -1 * shift_y),
              (shift_x, shift_y),
              (-1 * shift_x, shift_y)]
    
    result = np.zeros(4).astype(int)
    
    for i, shift in enumerate(search):
    
        corner = node + shift
        corner_node = _get_index(df, corner)
        
        if corner_node is None:
            raise RuntimeError("corner node not found")
        
        result[i] = corner_node
    
    return result


def _get_index(df: pd.DataFrame,
               node: npt.NDArray[np.float64]) -> Optional[int]:
    
    xcheck = np.isclose(df["x"], node[0])
    ycheck = np.isclose(df["y"], node[1])
    result = df[xcheck & ycheck]
    
    if result.empty: return None
    
    if len(result) > 1:
        raise RuntimeError("multiple matching indices")
    
    return result.index[0]
