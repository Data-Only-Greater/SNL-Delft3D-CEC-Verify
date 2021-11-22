# -*- coding: utf-8 -*-

# Copyright (c) 2019, Guus Rongen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import os
from ctypes import CDLL, byref, c_char, c_int, pointer
from itertools import combinations

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.prepared import prep

from .checks import check_argument
from .cstructures import meshgeom, meshgeomdim
from .geometry import (as_polygon_list,
                       minimum_bounds_fixed_rotation,
                       points_in_polygon,
                       rotate_coordinates)

logger = logging.getLogger(__name__)


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

    def clip_nodes(self, xnodes,
                         ynodes,
                         edge_nodes,
                         polygon,
                         keep_outside=False):
        """
        Method that returns a set of nodes that is clipped within a given
        polygon.
        
        Parameters
        ----------
        xnodes : 
            X-coordinates of mesh nodes
        ynodes : 
            Y-coordinates of mesh nodes
        edge_nodes : 
            node ids of edges. These are assumed in 1-based numbering
        polygon : Polygon, Multipolygon or list of
        
        """
        
        # Find nodes within one of the polygons
        logger.info('Selecting nodes within polygon.')
        index = np.zeros(len(xnodes), dtype=bool)
        for poly in as_polygon_list(polygon):
            index = index | points_in_polygon(np.c_[xnodes, ynodes], poly)
        if keep_outside:
            index = ~index
        
        # Filter edge nodes, keep the ones that are within a polygon with both points
        nodeids_in_polygon = np.where(index)[0] + 1
        edge_nodes = edge_nodes[np.isin(edge_nodes,
                                        nodeids_in_polygon).all(axis=1)]
        
        # Remove edges that have a 1 count, until none are left
        logger.info('Remove edges with only a single node within the clip '
                    'area.')
        unique, count = np.unique(edge_nodes, return_counts=True)
        while any(count == 1):
            count1nodes = unique[count == 1]
            edge_nodes = edge_nodes[~np.isin(edge_nodes,
                                             count1nodes).any(axis=1)]
            unique, count = np.unique(edge_nodes, return_counts=True)
        
        # Select remaining nodes
        xnodes = xnodes[unique - 1]
        ynodes = ynodes[unique - 1]
        
        # Make mapping for new id's
        new_id_mapping = {old_id: new_id + 1
                                  for new_id, old_id in enumerate(unique)}
        edge_nodes = np.reshape([new_id_mapping[old_id]
                                     for old_id in edge_nodes.ravel()],
                                edge_nodes.shape)
        
        return xnodes, ynodes, edge_nodes
    
    def clip_mesh_by_polygon(self, polygon, outside=True):
        """
        Removes part of the existing mesh within the given polygon.
        
        Parameters
        ----------
        polygon : list, Polygon, MultiPolygon
            A polygon, multi-polygon or list of multiple polygons or 
            multipolygons. The faces within the polygons are removed.
        """
        logger.info('Clipping 2D mesh by polygon.')
        
        # Check if the input arguments is indeed some kind of polygon
        check_argument(polygon, 'polygon', (list, Polygon, MultiPolygon))
        
        # Get xnodes, ynodes and edge_nodes
        xnodes = self.meshgeom.get_values('nodex', as_array=True)
        ynodes = self.meshgeom.get_values('nodey', as_array=True)
        edge_nodes = self.meshgeom.get_values('edge_nodes', as_array=True)
        
        # Clip
        logger.info('Clipping nodes.')
        xnodes, ynodes, edge_nodes = self.clip_nodes(xnodes,
                                                     ynodes,
                                                     edge_nodes,
                                                     polygon,
                                                     keep_outside=outside)
        # edge_nodes = np.sort(edge_nodes, axis=1)
        
        # Update dimensions
        self.meshgeomdim.numnode = len(xnodes)
        self.meshgeomdim.numedge = len(edge_nodes)
        
        # Add nodes and links
        self.meshgeom.set_values('nodex', xnodes)
        self.meshgeom.set_values('nodey', ynodes)
        self.meshgeom.set_values('edge_nodes', np.ravel(edge_nodes).tolist())
        
        # Determine what the cells are
        logger.info('Finding cell faces within clipped nodes.')
        self._find_cells(self.meshgeom)
        
        # Clean nodes, this function deletes nodes based on no longer existing
        # cells
        face_nodes = self.meshgeom.get_values('face_nodes', as_array=True)
        logger.info('Removing incomplete faces.')
        cleaned = self.clean_nodes(xnodes, ynodes, edge_nodes, face_nodes)
       
        # If cleaning leaves no whole cells, return None
        if cleaned is None:
            raise ValueError('Clipping the grid does not leave any nodes.')
        # Else, get the arguments from the returned tuple
        else:
            xnodes, ynodes, edge_nodes, face_nodes = cleaned
        
        logger.info('Update mesh with clipped nodes, edges and faces.')
        # Update dimensions
        self.meshgeomdim.numnode = len(xnodes)
        self.meshgeomdim.numedge = len(edge_nodes)
        
        # Add nodes and links
        self.meshgeom.set_values('nodex', xnodes)
        self.meshgeom.set_values('nodey', ynodes)
        self.meshgeom.set_values('edge_nodes', np.ravel(edge_nodes).tolist())
        self.meshgeom.set_values('face_nodes', np.ravel(face_nodes).tolist())
    
    def clean_nodes(self, xnodes, ynodes, edge_nodes, face_nodes):
        """
        Method to clean the nodes. Edges that do not form a cell are deleted.
        Alternative method based on checking tuple pairs
        """
        
        # Select nodes the occur in any face
        node_selection = np.unique(face_nodes)
        node_selection = node_selection[node_selection!=-999]
        # If no nodes (because no faces), return None
        if not node_selection.any():
            return None
        
        # Remove all edges that are not in this selection
        edge_nodes = edge_nodes[np.isin(edge_nodes,
                                        node_selection).all(axis=1)]
                
        # Remove all segments that are not part of any face
        # Direction is irrelevant, sort to compare in ascending order
        # Convert to a contiguous array for faster comparison
        dtype = np.dtype((np.void,
                          edge_nodes.dtype.itemsize * edge_nodes.shape[1]))
        sorted_edges = np.ascontiguousarray(
                                    np.sort(edge_nodes, axis=1)).view(dtype)
        idx = np.zeros(len(sorted_edges), dtype=bool)
        
        # Get combinations of face nodes that can form an edge
        combs = list(combinations(range(len(face_nodes[0])), 2))
        
        for comb in combs:
            # Get the first, second, third, etc. possible edge of every face
            arr = face_nodes[:, comb]
            # Remove nodata (so for example the non-existing fourth edge of a
            # triangular face)
            arr = arr[(arr != -999).all(axis=1)]
            arr = np.sort(arr, axis=1)
            # Convert to a contiguous array for faster comparison
            dtype = np.dtype((np.void, arr.dtype.itemsize * arr.shape[1]))
            sorted_face_edges = np.ascontiguousarray(arr).view(dtype)
            # Check if face edges are in edges
            idx |= np.isin(sorted_edges, sorted_face_edges)[:, 0]
        
        # Select the nodes that are present in faces
        edge_nodes = edge_nodes[idx]
        
        xnodes = xnodes[node_selection - 1]
        ynodes = ynodes[node_selection - 1]
        
        # Make mapping for new id's
        new_id_mapping = {old_id: new_id + 1
                              for new_id, old_id in enumerate(node_selection)}
        
        remap = lambda x: np.reshape(
            [-999 if old_id == -999 else new_id_mapping[old_id]
                                                     for old_id in x.ravel()],
            x.shape)
        
        edge_nodes = remap(edge_nodes)
        face_nodes = remap(face_nodes)
        
        return xnodes, ynodes, edge_nodes, face_nodes
    
    @staticmethod
    def _find_cells(geometries, maxnumfacenodes=None):
        """
        Determine what the cells are in a grid.
        """
        
        dimensions = geometries.meshgeomdim
        
        wrapperGridgeom = CDLL(os.path.join(os.path.dirname(__file__),
                                            'gridgeom.dll'))
        ierr = wrapperGridgeom.ggeo_deallocate()
        assert ierr == 0
        
        start_index = c_int(1)
        
        meshdimout = meshgeomdim()
        meshout = meshgeom(meshdimout)
        
        ierr = wrapperGridgeom.ggeo_find_cells(byref(dimensions),
                                               byref(geometries),
                                               byref(meshdimout),
                                               byref(meshout),
                                               byref(start_index))
        assert ierr == 0
        
        dimensions.numface = meshdimout.numface
        
        if maxnumfacenodes is None:
            dimensions.maxnumfacenodes = meshdimout.maxnumfacenodes
        else:
            dimensions.maxnumfacenodes = maxnumfacenodes
        
        # Allocate
        for mesh in [geometries, meshout]:
            for var in ['facex', 'facey', 'face_nodes']:
                mesh.allocate(var)
        
        ierr = wrapperGridgeom.ggeo_find_cells(byref(dimensions),
                                               byref(geometries),
                                               byref(meshdimout),
                                               byref(meshout),
                                               byref(start_index))
        assert ierr == 0
        
        # Copy content to self meshgeom
        for var in ['facex', 'facey', 'face_nodes']:
            # Create array of allocated size. In case of deviating
            # maxnumfacenodes
            if (maxnumfacenodes is not None) and (var == 'face_nodes'):
                # Create an empty integer. Empty values should only be present
                # in the integer arrays
                arr = np.full(geometries.get_dimensions(var), -999, dtype=int)
                # Get array
                arr[:, :meshout.meshgeomdim.maxnumfacenodes] = \
                                    meshout.get_values(var, as_array=True)
                # Set array
                geometries.set_values(var, arr.ravel())
            else:
                # Set array
                geometries.set_values(var, meshout.get_values(var))
        
        ierr = wrapperGridgeom.ggeo_deallocate()
        assert ierr == 0
    
    def altitude_constant(self, constant, where='face'):
        zvalues = np.ones(getattr(self.meshgeomdim, f'num{where}')) * constant
        self.meshgeom.set_values(f'{where}z', zvalues)
    
    def set_missing_z_value(self, value):
        self.missing_z_value = value
    
    def faces_to_centroid(self):
        """
        The find_cells function does not always return face coordinates
        that are all accepted by the interactor. The coordinates
        are placed on the circumcenters, and placed on the face border
        in case of a coordinate that is outside the cells.
        
        This function shifts the face coordinates towards the centroid
        (center of gravity) of the cell.
        """
        # Calculate centroids
        centroids = np.vstack([cell.mean(axis=0)
                                   for cell in self.meshgeom.get_faces()]).T
        
        # Set values back to geometry
        self.meshgeom.set_values('facex', centroids[0])
        self.meshgeom.set_values('facey', centroids[1])


class Rectangular(Mesh2D):
    
    def __init__(self):
        Mesh2D.__init__(self)
        self.meshgeomdim.maxnumfacenodes = 4
        self.rotated = False
        
    def generate_grid(self, x0,
                            y0,
                            dx,
                            dy,
                            ncols,
                            nrows,
                            clipgeo=None,
                            rotation=0):
        """
        Generate rectangular grid based on the origin (x0, y0) the cell sizes (dx, dy),
        the number of columns and rows (ncols, nrows) and a rotation in degrees (default=0)
        A geometry (clipgeo) can be given to clip the grid.
        """
        
        # Generate x and y spacing
        x = np.linspace(x0, x0 + dx * (ncols), ncols+1)
        y = np.linspace(y0, y0 + dy * (nrows), nrows+1)
        
        # Get nodes
        xnodes, ynodes = np.meshgrid(x, y)
        
        # Rotate
        if rotation != 0:
            self.rotated = True
            xnodes, ynodes = rotate_coordinates((x0, y0),
                                                np.radians(rotation),
                                                xnodes,
                                                ynodes)
        
        # Get nodes as list
        nodes = {crd: i+1 for i, crd in enumerate(zip(xnodes.ravel(),
                                                      ynodes.ravel()))}
        
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
        
        # Rvael the nodes
        xnodes = xnodes.ravel()
        ynodes = ynodes.ravel()
        
        # Add to mesh
        dimensions = meshgeomdim()
        dimensions.dim = 2
        geometries = meshgeom(dimensions)
        
        # Clip
        if clipgeo is not None:
            xnodes, ynodes, edge_nodes = self.clip_nodes(xnodes,
                                                         ynodes,
                                                         edge_nodes,
                                                         clipgeo)
        
        # Update dimensions
        dimensions.numnode = len(xnodes)
        dimensions.numedge = len(edge_nodes)

        # Add nodes and links
        geometries.set_values('nodex', xnodes)
        geometries.set_values('nodey', ynodes)
        geometries.set_values('edge_nodes', np.ravel(edge_nodes).tolist())
        
        # Determine what the cells are
        self._find_cells(geometries)
        
        # Clip
        if clipgeo is not None:
            # Clean nodes, this function deletes nodes based on no longer
            # existing cells
            face_nodes = geometries.get_values('face_nodes', as_array=True)
            cleaned = self.clean_nodes(xnodes, ynodes, edge_nodes, face_nodes)
            # If cleaning leaves no whole cells, return None
            if cleaned is None:
                return None
            # Else, get the arguments from the returned tuple
            else:
                xnodes, ynodes, edge_nodes, face_nodes = cleaned
        
        # Update dimensions
        dimensions.numnode = len(xnodes)
        dimensions.numedge = len(edge_nodes)
        dimensions.maxnumfacenodes = 4
        
        # Add nodes and links
        geometries.set_values('nodex', xnodes)
        geometries.set_values('nodey', ynodes)
        geometries.set_values('edge_nodes', np.ravel(edge_nodes).tolist())
        geometries.set_values('face_nodes', np.ravel(face_nodes).tolist())
        
        # Add to mesh
        self.meshgeom.add_from_other(geometries)
    
    def generate_within_polygon(self, polygon, dx, dy, rotation=0):
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
        
        logger.info(f'Generating grid with cellsize {dx}x{dy} m and rotation '
                    f'{rotation} degrees.')
        convex = MultiPolygon(polygons).convex_hull
        
        # In case of a rotation, extend the grid far enough to make sure
        if rotation != 0:
            # Find a box that contains the whole polygon
            (x0, y0), xsize, ysize = minimum_bounds_fixed_rotation(convex,
                                                                   rotation)
        else:
            xsize = convex.bounds[2] - convex.bounds[0]
            ysize= convex.bounds[3] - convex.bounds[1]
            x0, y0 = convex.bounds[0], convex.bounds[1]
        
        self.generate_grid(x0=x0,
                           y0=y0,
                           dx=dx,
                           dy=dy,
                           ncols=int(xsize / dx) + 1,
                           nrows=int(ysize / dy) + 1,
                           clipgeo=polygon,
                           rotation=rotation)
