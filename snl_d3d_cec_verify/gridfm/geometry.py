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

import numpy as np
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.prepared import prep

logger = logging.getLogger(__name__)


def rotate_coordinates(origin, theta, xcrds, ycrds):
    """
    Rotate coordinates around origin (x0, y0) with a certain angle (radians)
    """
    
    x0, y0 = origin
    xcrds_rot = x0 + (xcrds - x0) * np.cos(theta) + \
                                                (ycrds - y0) * np.sin(theta)
    ycrds_rot = y0 - (xcrds - x0) * np.sin(theta) + \
                                                (ycrds - y0) * np.cos(theta)
    
    return xcrds_rot, ycrds_rot


def minimum_bounds_fixed_rotation(polygon, angle):
    """Get the minimum box for a polygon with a given axes rotation.
    
    Parameters
    ----------
    polygon : shapely.geometry.Polygon
        Polygon that is rotated
    angle : int or float
        Rotation of the polygon in degrees
        
    Returns
    -------
    tuple
        Tuple with origin (x, y), xsize and ysize
    """
    # Determine spinning point
    spinpt = (polygon.envelope.bounds[0], polygon.envelope.bounds[1])
    
    # Rotate clip polygon with rotation, get envelope and rotate back.
    rotbox1 = affinity.rotate(polygon, angle=angle, origin=spinpt).envelope
    
    # Determine size of grid
    xsize = rotbox1.bounds[2] - rotbox1.bounds[0]
    ysize = rotbox1.bounds[3] - rotbox1.bounds[1]
    
    # Rotate again, and get origin
    rotbox2 = affinity.rotate(rotbox1, angle=-angle, origin=spinpt)
    origin = rotbox2.exterior.coords[0]
    
    return origin, xsize, ysize


def points_in_polygon(points, polygon):
    """
    Determine points that are inside a polygon, taking
    holes into account.
    
    Parameters
    ----------
    points : numpy.array
        Nx2 - array
    polygon : shapely.geometry.Polygon
        Polygon (can have holes)
    """
    # First select points in square box around polygon
    ptx, pty = points.T
    mainindex = possibly_intersecting(
        dataframebounds=np.c_[[ptx, pty, ptx, pty]], geometry=polygon)
    boxpoints = points[mainindex]
    
    extp = prep(Polygon(polygon.exterior))
    intps = [prep(Polygon(interior)) for interior in polygon.interiors]
    
    # create first index. Everything within exterior is True
    index = np.array([extp.intersects(Point(*x)) for x in boxpoints])
    
    # set points in holes also to nan
    if intps:
        subset = boxpoints[index]
        # Start with all False
        subindex = np.zeros(len(subset), dtype=bool)
        
        for intp in intps:
            # update mask, set to True where point in interior
            subindex = subindex | np.array([extp.intersects(Point(*x))
                                                            for x in subset])
        
        # Everything within interiors should be True
        # So, set everything within interiors (subindex == True), to True
        index[np.where(index)[0][subindex]] = False
    
    # Set index in main index to False
    mainindex[np.where(mainindex)[0][~index]] = False
    
    return mainindex


def possibly_intersecting(dataframebounds, geometry, buffer=1e-4):
    """
    Finding intersecting profiles for each branch is a slow process in case of 
    large datasets. To speed this up, we first determine which profile 
    intersect a square box around the branch. With the selection, the 
    interseting profiles can be determines much faster.
    
    Parameters
    ----------
    dataframebounds : numpy.array
    geometry : shapely.geometry.Polygon
    """
    
    geobounds = geometry.bounds
    idx = (
        (dataframebounds[0] - buffer < geobounds[2]) &
        (dataframebounds[2] + buffer > geobounds[0]) &
        (dataframebounds[1] - buffer < geobounds[3]) &
        (dataframebounds[3] + buffer > geobounds[1])
    )
    # Get intersecting profiles
    return idx


def as_polygon_list(polygon):
    return as_geometry_list(polygon, Polygon, MultiPolygon)


def as_geometry_list(geometry, singletype, multitype):
    """Convenience method to return a list with one or more
    
    Polygons/LineString/Point from a given Polygon/LineString/Point
    or MultiPolygon/MultiLineString/MultiPoint.
    
    Parameters
    ----------
    polygon : list or Polygon or MultiPolygon
        Object to be converted
    
    Returns
    -------
    list
        list of Polygons
    """
    if isinstance(geometry, singletype):
        return [geometry]
    elif isinstance(geometry, multitype):
        return [p for p in geometry]
    elif isinstance(geometry, list):
        lst = []
        for item in geometry:
            lst.extend(as_geometry_list(item, singletype, multitype))
        return lst
    else:
        raise TypeError(f'Expected {singletype} or {multitype}. Got '
                        f'"{type(geometry)}"')
