# -*- coding: utf-8 -*-

# Copyright (c) 2019, Guus Rongen

from shapely.geometry import MultiPolygon, Polygon # type: ignore


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
