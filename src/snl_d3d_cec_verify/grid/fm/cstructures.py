# -*- coding: utf-8 -*-

# Copyright (c) 2019, Guus Rongen

from ctypes import POINTER, Structure, c_char, c_double, c_int

import numpy as np


# Definieer load structure
class meshgeomdim(Structure):
    
    _fields_ = [
        ('meshname', POINTER(c_char)),
        ('dim', c_int),
        ('numnode', c_int),
        ('numedge', c_int),
        ('numface', c_int),
        ('maxnumfacenodes', c_int),
        ('numlayer', c_int),
        ('layertype', c_int),
        ('nnodes', c_int),
        ('nbranches', c_int),
        ('ngeometry', c_int),
        ('epgs', c_int)
    ]


class meshgeom(Structure):
    _fields_ = [
        ('edge_nodes', POINTER(c_int)),
        ('face_nodes', POINTER(c_int)),
        ('edge_faces', POINTER(c_int)),
        ('face_edges', POINTER(c_int)),
        ('face_links', POINTER(c_int)),
        ('nnodex', POINTER(c_double)),
        ('nnodey', POINTER(c_double)),
        ('nedge_nodes', POINTER(c_int)),
        ('nbranchlengths', POINTER(c_double)),
        ('nbranchgeometrynodes', POINTER(c_int)),
        ('ngeopointx', POINTER(c_double)),
        ('ngeopointy', POINTER(c_double)),
        ('nbranchorder', POINTER(c_double)),
        ('branchidx', POINTER(c_int)),
        ('branchoffsets', POINTER(c_double)),
        #('edge_branchidx', POINTER(c_int)),
        #('edge_branchoffsets', POINTER(c_double)),
        ('nodex', POINTER(c_double)),
        ('nodey', POINTER(c_double)),
        ('nodez', POINTER(c_double)),
        ('edgex', POINTER(c_double)),
        ('edgey', POINTER(c_double)),
        ('edgez', POINTER(c_double)),
        ('facex', POINTER(c_double)),
        ('facey', POINTER(c_double)),
        ('facez', POINTER(c_double)),
        ('layer_zs', POINTER(c_int)),
        ('interface_zs', POINTER(c_int))
    ]
    
    def __init__(self, geometries):
        """
        Constructor
        """
        
        self.meshgeomdim = geometries
        
        # This dictionary contains some extra variables for 1d meshes
        self.description1d = {
            'mesh1d_node_ids': [],
            'mesh1d_node_long_names': [],
            'network_node_ids': [],
            'network_node_long_names': [],
            'network_branch_ids': [],
            'network_branch_long_names': []
        }
        
        self._meta_ = {
            'nodex': {'ctype': c_double, 'size': ['numnode'], 'allocated': False},
            'nodey': {'ctype': c_double, 'size': ['numnode'], 'allocated': False},
            'nodez': {'ctype': c_double, 'size': ['numnode'], 'allocated': False},
            'branchoffsets': {'ctype': c_double, 'size': ['numnode'], 'allocated': False},
            'branchidx': {'ctype': c_int, 'size': ['numnode'], 'allocated': False},            
            #'edge_branchoffsets': {'ctype': c_double, 'size': ['numedge'], 'allocated': False},
            #'edge_branchidx': {'ctype': c_int, 'size': ['numedge'], 'allocated': False},
            'nnodex': {'ctype': c_double, 'size': ['nnodes'], 'allocated': False},
            'nnodey': {'ctype': c_double, 'size': ['nnodes'], 'allocated': False},
            'ngeopointx': {'ctype': c_double, 'size': ['ngeometry'], 'allocated': False},
            'ngeopointy': {'ctype': c_double, 'size': ['ngeometry'], 'allocated': False},
            'nbranchlengths': {'ctype': c_double, 'size': ['nbranches'], 'allocated': False},
            'nbranchorder': {'ctype': c_double, 'size': ['nbranches'], 'allocated': False},
            'edgex': {'ctype': c_double, 'size': ['numedge'], 'allocated': False},
            'edgey': {'ctype': c_double, 'size': ['numedge'], 'allocated': False},
            'edgez': {'ctype': c_double, 'size': ['numedge'], 'allocated': False},
            'nedge_nodes': {'ctype': c_int, 'size': ['nbranches', 2], 'allocated': False},
            'nbranchgeometrynodes': {'ctype': c_int, 'size': ['nbranches'], 'allocated': False},
            'facex': {'ctype': c_double, 'size': ['numface'], 'allocated': False},
            'facey': {'ctype': c_double, 'size': ['numface'], 'allocated': False},
            'facez': {'ctype': c_double, 'size': ['numface'], 'allocated': False},
            'face_nodes': {'ctype': c_int, 'size': ['numface', 'maxnumfacenodes'], 'allocated': False},
            'edge_nodes': {'ctype': c_int, 'size': ['numedge', 2], 'allocated': False},
            'edge_faces': {'ctype': c_int, 'size': ['numedge', 2], 'allocated': False},
            'face_edges': {'ctype': c_int, 'size': ['numface', 'maxnumfacenodes'], 'allocated': False}
        }
    
    def get_dimensions(self, var):
        return tuple(getattr(self.meshgeomdim, fac) if isinstance(fac, str) else fac for fac in self._meta_[var]['size'])
    
    def get_size(self, var):
        return np.prod(self.get_dimensions(var))
    
    def allocate(self, var):
        ctype = self._meta_[var]['ctype']
        size = self.get_size(var)
        setattr(self, var, (ctype * size)())
        self._meta_[var]['allocated'] = True
    
    def is_allocated(self, var):
        return self._meta_[var]['allocated']
    
    def get_values(self, var, as_array=False, size=None):
        if not self.is_allocated(var):
            return None
        size = self.get_size(var) if size is None else size
        values = [getattr(self, var)[i] for i in range(size)]
        if as_array:
            values = np.reshape(values, self.get_dimensions(var))
        return values
    
    def set_values(self, var, values):
        # First allocate
        self.allocate(var)
        
        size = self.get_size(var)
        if size != len(values):
            raise ValueError(f'Size of values ({len(values)}) does not match allocated size ({size}) for "{var}".')
        for i, value in enumerate(values):
            getattr(self, var)[i] = value
    
    def add_values(self, var, values):
        
        # If not yet allocated, don't add but set
        if not self.is_allocated(var):
            self.set_values(var, values)
        
        # Get old values
        old_values = self.get_values(var, size=(self.get_size(var)-len(values)))
        
        # First allocate
        self.allocate(var)
        size = self.get_size(var)
        
        if size != (len(values) + len(old_values)):
            raise ValueError(f'Size of values ({len(values) + len(old_values)}) does not match allocated size ({size})')
        
        for i, value in enumerate(old_values + values):
            getattr(self, var)[i] = value
    
    def add_from_other(self, geometries):
        """
        Method to merge mesh with another mesh
        """
        
        # If the current mesh is empty, copy the maxfacenumnodes
        if self.empty():
            self.meshgeomdim.maxnumfacenodes = geometries.meshgeomdim.maxnumfacenodes
        # If the maxnumfacenodes is not equal, raise an error. Merging two diffently shaped meshes not implemented
        if self.meshgeomdim.maxnumfacenodes != geometries.meshgeomdim.maxnumfacenodes:
            raise NotImplementedError('The maximum number of face nodes differs between the meshes.')
        
        # Get the counter offset for the nodes
        startnode = self.meshgeomdim.numnode
        
        # Add dimensions. Sum the new dimensions with the old ones
        for dimension in ['numnode', 'numedge', 'numface', 'nnodes', 'ngeometry', 'nbranches']:
            new = getattr(self.meshgeomdim, dimension) + getattr(geometries.meshgeomdim, dimension)
            setattr(self.meshgeomdim, dimension, new)
        
        # Add variables. Add all new data
        for var in ['nodex', 'nodey', 'nodez', 'facex', 'facey', 'facez', 'nnodex', 'nnodey',
                    'nbranchlengths', 'nbranchorder', 'ngeopointx', 'ngeopointy', 'nbranchgeometrynodes']:
            if geometries.is_allocated(var):
                self.add_values(var, geometries.get_values(var))
        
        # For variables with indexes. For the indexes, add the old start node
        for indexvar in ['edge_nodes', 'face_nodes', 'branchidx', 'branchoffsets']:
            if geometries.is_allocated(indexvar):
                self.add_values(indexvar, [i + startnode for i in geometries.get_values(indexvar)]) 
    
    def empty(self):
        """Determine whether mesh is empty, based on number of nodes"""
        return not bool(self.meshgeomdim.numnode)
