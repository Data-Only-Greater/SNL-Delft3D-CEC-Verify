# -*- coding: utf-8 -*-

import pandas as pd
import pytest
import geopandas as gpd
from shapely.geometry import LineString

from snl_d3d_cec_verify.result.edges import map_to_edges_geoframe, Edges


def test_map_to_edges_geoframe(data_dir):
    
    map_path = data_dir / "output" / "FlowFM_map.nc"
    gdf = map_to_edges_geoframe(map_path, -1)
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 498
    assert gdf.columns.to_list() == ["geometry", "k", "time", "u1", "n0", "n1"]
    assert set(gdf["geometry"].apply(lambda x: x.geom_type)) == \
                                                        set(['LineString'])
    assert set(gdf["k"]) == set([0, 1, 2])
    assert set(gdf["time"]) == set([pd.Timestamp('2001-01-01 01:00:00')])
    assert gdf["u1"].min() > -0.9
    assert gdf["u1"].max() < 0.9
    assert set(gdf["n0"]) == set([0., -1., 1.])
    assert set(gdf["n1"]) == set([0., -1., 1.])


@pytest.fixture
def edges(data_dir):
    map_path = data_dir / "output" / "FlowFM_map.nc"
    return Edges(map_path, 2)


def test_edges_load_t_step_first(edges):
    
    t_step = -1
    expected_t_step = edges.resolve_t_step(t_step)
    edges._load_t_step(t_step)
    
    assert len(edges._frame) == 498
    assert expected_t_step in edges._t_steps
    assert edges._t_steps[expected_t_step] == \
                                        pd.Timestamp('2001-01-01 01:00:00')


def test_edges_load_t_step_second(edges):
    
    edges._load_t_step(-1)
    edges._load_t_step(0)
    
    assert len(edges._frame) == 498 * 2
    assert len(edges._t_steps) == 2
    assert set(edges._frame["time"]) == set([
                                        pd.Timestamp('2001-01-01 01:00:00'),
                                        pd.Timestamp('2001-01-01')])


def test_edges_load_t_step_no_repeat(edges):
    
    edges._load_t_step(-1)
    edges._load_t_step(1)
    
    assert len(edges._frame) == 498
    assert len(edges._t_steps) == 1


def test_edges_extract_k_no_geom(edges):
    
    gdf = edges.extract_k(-1, 0)
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 166
    assert gdf.columns.to_list() == ["geometry", "u1", "n0", "n1"]
    assert set(gdf["geometry"].apply(lambda x: x.geom_type)) == \
                                                        set(['LineString'])
    assert gdf["u1"].min() > -0.9
    assert gdf["u1"].max() < 0.9
    assert set(gdf["n0"]) == set([0., -1., 1.])
    assert set(gdf["n1"]) == set([0., -1., 1.])


def test_edges_extract_k_line(edges):
    
    centreline = LineString(((0, 3), (18, 3)))
    gdf = edges.extract_k(-1, 0, centreline)
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 19
    assert gdf.columns.to_list() == ["geometry", "u1"]
    assert gdf["u1"].min() > -0.9
    assert gdf["u1"].max() < 0.9
    assert set(gdf["geometry"].apply(lambda x: x.geom_type)) == \
                                                        set(['Point'])
    
    wkt = gdf["geometry"].apply(lambda geom: geom.wkt)
    assert len(set(wkt)) == 19
