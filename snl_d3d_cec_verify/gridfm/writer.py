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

import os
from contextlib import contextmanager

import numpy as np
from netCDF4 import Dataset

from .checks import check_argument
from .cstructures import meshgeom, meshgeomdim


def write2D(twodmesh, path, version):
    
    mesh2d = meshgeom(meshgeomdim())
    mesh2d.meshgeomdim.dim = 2
    
    if not hasattr(twodmesh, 'meshgeom'):
        check_argument(twodmesh, 'twodmesh', meshgeom)
        geometries = twodmesh
    else:
        if not isinstance(twodmesh.meshgeom, meshgeom):
            raise TypeError('The given mesh should have an attribute '
                            '"meshgeom".')
        geometries = twodmesh.meshgeom
    
    mesh2d.add_from_other(geometries)
    
    with create_netcdf(path, version) as ncfile:
        init_shared(ncfile)
        init_2dmesh(ncfile, mesh2d)
        set_2dmesh(ncfile, mesh2d)


@contextmanager
def create_netcdf(path, version):
    
    # File format:
    outformat = "NETCDF4"
    # File where we going to write
    ncfile = Dataset(path, 'w', format=outformat)
    
    # global attributes   (conventions must be CF-1.8 UGRID-1.0 Deltares-0.10
    #                      for the GUI)
    ncfile.Conventions = "CF-1.8 UGRID-1.0 Deltares-0.10"
    ncfile.title = 'Delft3D-FM 1D2D network for model ' + \
                                    os.path.split(path)[-1].rstrip('_net.nc')
    ncfile.source = (f"delft3dfmpy v.{version['number']}, D-HyDAMO, model "
                     f"{os.path.split(path)[-1].rstrip('_net.nc')}")
    ncfile.history = (f"Created on {version['date']} by "
                      f"{os.path.split(__file__)[-1]}.")
    ncfile.institution = "Deltares/HKV"
    ncfile.references = ("https://github.com/openearth/delft3dfmpy/; "
                         "https://www.deltares.nl; https://www.hkv.nl")
    ncfile.comment = (f"Tested and compatible with D-Flow FM "
                      f"{version['dfm_version']}, DIMRset "
                      f"{version['dimr_version']} and D-HYDRO suite 1D2D "
                      f"{version['suite_version']}")
    
    try:
        yield ncfile
    finally:
        ncfile.close()


def init_shared(ncfile):
    ncfile.createDimension("Two", 2)


def init_2dmesh(ncfile, cmesh2d):
    
    ncfile.createDimension("max_nmesh2d_face_nodes",
                           cmesh2d.meshgeomdim.maxnumfacenodes)
    ncfile.createDimension("mesh2d_nEdges", cmesh2d.meshgeomdim.numedge)
    ncfile.createDimension("mesh2d_nFaces", cmesh2d.meshgeomdim.numface)
    ncfile.createDimension("mesh2d_nNodes", cmesh2d.meshgeomdim.numnode)


def set_2dmesh(ncfile, cmesh2d):
    
    mesh2d = ncfile.createVariable("mesh2d", "i4", ())
    mesh2d.long_name = "Topology data of 2D network"
    mesh2d.topology_dimension = 2
    mesh2d.cf_role = 'mesh_topology'
    mesh2d.node_coordinates = 'mesh2d_node_x mesh2d_node_y'
    mesh2d.node_dimension = 'mesh2d_nNodes'
    mesh2d.edge_coordinates = 'mesh2d_edge_x mesh2d_edge_y'
    mesh2d.edge_dimension = 'mesh2d_nEdges'
    mesh2d.edge_node_connectivity = 'mesh2d_edge_nodes'
    mesh2d.face_node_connectivity = 'mesh2d_face_nodes'
    mesh2d.max_face_nodes_dimension = 'max_nmesh2d_face_nodes'
    mesh2d.face_dimension = "mesh2d_nFaces"
    #mesh2d.edge_face_connectivity = "mesh2d_edge_faces"
    mesh2d.face_coordinates = "mesh2d_face_x mesh2d_face_y"
    
    # Nodes:
    mesh2d_x = ncfile.createVariable("mesh2d_node_x",
                                     np.float64,
                                     mesh2d.node_dimension)
    mesh2d_y = ncfile.createVariable("mesh2d_node_y",
                                     np.float64,
                                     mesh2d.node_dimension)
    mesh2d_z = ncfile.createVariable("mesh2d_node_z",
                                     np.float64,
                                     mesh2d.node_dimension,
                                     fill_value=-999.0)
    
    mesh2d_x.standard_name = 'projection_x_coordinate'
    mesh2d_y.standard_name = 'projection_y_coordinate'
    mesh2d_z.standard_name = 'altitude'
    
    for var, dim in zip([mesh2d_x, mesh2d_y, mesh2d_z],  list('xyz')):
        setattr(var, 'units', 'm')
        setattr(var, 'mesh', 'mesh2d')
        setattr(var, 'location', 'node')
        setattr(var, 'long_name', f'{dim}-coordinate of mesh nodes')
    
    mesh2d_z.coordinates = 'mesh2d_node_x mesh2d_node_y'
    mesh2d_z.grid_mapping = ''
    
    mesh2d_x[:] = cmesh2d.get_values("nodex")
    mesh2d_y[:] = cmesh2d.get_values("nodey")
    
    # Edges:
    # mesh2d_xu = ncfile.createVariable("mesh2d_edge_x", np.float64,  "nmesh2d_edges")
    # mesh2d_yu = ncfile.createVariable("mesh2d_edge_y", np.float64,  "nmesh2d_edges")
    # mesh2d_xu[:] = cmesh2d.get_values("edgex")
    # mesh2d_yu[:] = cmesh2d.get_values("edgey")
    # mesh2d_xu.long_name = 'x-coordinate of mesh edges'
    # mesh2d_yu.long_name = 'y-coordinate of mesh edges'
    
    # for var, dim in zip([mesh2d_xu, mesh2d_yu],  list('xy')):
    #     setattr(var, 'units', 'm')
    #     setattr(var, 'mesh', 'mesh2d')
    #     setattr(var, 'location', 'edge')
    #     setattr(var, 'standard_name', f'projection_{dim}_coordinate')
    
    mesh2d_en = ncfile.createVariable("mesh2d_edge_nodes",
                                      "i4",
                                      (mesh2d.edge_dimension, "Two"),
                                      fill_value=-999)
    mesh2d_en.cf_role = 'edge_node_connectivity'
    mesh2d_en.long_name = 'maps every edge to the two nodes that it connects'
    mesh2d_en.start_index = 1
    mesh2d_en.location = 'edge'
    mesh2d_en.mesh = 'mesh2d'
    
    mesh2d_en[:] = cmesh2d.get_values('edge_nodes', as_array=True)
    
    # mesh2d_et = ncfile.createVariable("mesh2d_edge_types", "i4", mesh2d.edge_dimension)
    # mesh2d_et.long_name = 'edge type (relation between edge and flow geometry)'
    # mesh2d_et.coordinates = 'mesh2d_edge_x mesh2d_edge_y'
    # mesh2d_et.location = 'edge'
    # mesh2d_et.mesh = 'mesh2d'
    # mesh2d_et.standard_name = ''
    # mesh2d_et.units = ''
    # mesh2d_et[:] = 2
    
    mesh2d_fn = ncfile.createVariable("mesh2d_face_nodes",
                                      "i4",
                                      (mesh2d.face_dimension,
                                       mesh2d.max_face_nodes_dimension),
                                      fill_value=-999)
    mesh2d_fn.cf_role = 'face_node_connectivity'
    mesh2d_fn.mesh = 'mesh2d'
    mesh2d_fn.location = 'face'
    mesh2d_fn.long_name = 'maps every face to the nodes that it defines'
    mesh2d_fn.start_index = 1
    mesh2d_fn[:] = cmesh2d.get_values('face_nodes', as_array=True)
    
    mesh2d_face_x = ncfile.createVariable("mesh2d_face_x",
                                          np.float64,
                                          mesh2d.face_dimension)
    mesh2d_face_y = ncfile.createVariable("mesh2d_face_y",
                                          np.float64,
                                          mesh2d.face_dimension)
    mesh2d_face_z = ncfile.createVariable("mesh2d_face_z",
                                          np.float64,
                                          mesh2d.face_dimension,
                                          fill_value=-999.0)
    
    for var, dim in zip([mesh2d_face_x, mesh2d_face_y, mesh2d_face_z],
                        list('xyz')):
        setattr(var, 'units', 'm')
        setattr(var, 'mesh', 'mesh2d')
        setattr(var, 'location', 'face')
        setattr(var, 'standard_name', f'projection_{dim}_coordinate'
                                                if dim != 'z' else 'altitude')
        setattr(var, 'long_name', f'{dim}-coordinate of face nodes')
    
    mesh2d_face_z.coordinates = 'mesh2d_face_x mesh2d_face_y'
    mesh2d_face_z.grid_mapping = ''
    
    mesh2d_face_x[:] = cmesh2d.get_values("facex")
    mesh2d_face_y[:] = cmesh2d.get_values("facey")
    
    # Assign altitude data
    # To faces
    if cmesh2d.is_allocated('facez'):
        mesh2d_face_z[:] = cmesh2d.get_values("facez")
    # Assign to nodes
    if cmesh2d.is_allocated('nodez'):
        mesh2d_z[:] = cmesh2d.get_values("nodez")
    # Raise error if none of both is allocated
    if not cmesh2d.is_allocated('nodez') and not cmesh2d.is_allocated('facez'):
        raise ValueError('Assign altitude values either to nodes or faces.')
