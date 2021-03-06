# -*- coding: utf-8 -*-

import warnings

import pandas as pd
import pytest
from shapely.geometry import LineString

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import geopandas as gpd

from snl_d3d_cec_verify.result.edges import _map_to_edges_geoframe, Edges


def test_map_to_edges_geoframe(data_dir):
    
    map_path = data_dir / "output" / "FlowFM_map.nc"
    gdf = _map_to_edges_geoframe(map_path, -1)
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == (4 * 19 + 5 * 18) * 7
    assert gdf.columns.to_list() == ["geometry",
                                     "sigma",
                                     "time",
                                     "u1",
                                     "turkin1",
                                     "n0",
                                     "n1",
                                     "f0",
                                     "f1"]
    assert set(gdf["geometry"].apply(lambda x: x.geom_type)) == \
                                                        set(['LineString'])
    assert set(gdf["sigma"]) == set([-1.0,
                                     -0.8333333333333334,
                                     -0.6666666666666667,
                                     -0.5,
                                     -0.33333333333333337,
                                     -0.16666666666666669,
                                      0.0])
    assert set(gdf["time"]) == set([pd.Timestamp('2001-01-01 01:00:00')])
    assert gdf["u1"].min() > -0.9
    assert gdf["u1"].max() < 0.9
    assert set(gdf["n0"]) == set([0., -1., 1.])
    assert set(gdf["n1"]) == set([0., -1., 1.])


def test_map_to_edges_geoframe_none(data_dir):
    
    map_path = data_dir / "output" / "FlowFM_map.nc"
    gdf = _map_to_edges_geoframe(map_path)
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == (4 * 19 + 5 * 18) * 7 * 2
    assert gdf.columns.to_list() == ["geometry",
                                     "sigma",
                                     "time",
                                     "u1",
                                     "turkin1",
                                     "n0",
                                     "n1",
                                     "f0",
                                     "f1"]
    assert set(gdf["geometry"].apply(lambda x: x.geom_type)) == \
                                                        set(['LineString'])
    assert set(gdf["sigma"]) == set([-1.0,
                                     -0.8333333333333334,
                                     -0.6666666666666667,
                                     -0.5,
                                     -0.33333333333333337,
                                     -0.16666666666666669,
                                      0.0])
    assert set(gdf["time"]) == set([pd.Timestamp('2001-01-01 00:00:00'),
                                    pd.Timestamp('2001-01-01 01:00:00')])
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
    expected_t_step = edges._resolve_t_step(t_step)
    edges._load_t_step(t_step)
    
    assert len(edges._frame) == (4 * 19 + 5 * 18) * 7
    assert expected_t_step in edges._t_steps
    assert edges._t_steps[expected_t_step] == \
                                        pd.Timestamp('2001-01-01 01:00:00')


def test_edges_load_t_step_second(edges):
    
    edges._load_t_step(-1)
    edges._load_t_step(0)
    
    assert len(edges._frame) == (4 * 19 + 5 * 18) * 7 * 2
    assert len(edges._t_steps) == 2
    assert set(edges._frame["time"]) == set([
                                        pd.Timestamp('2001-01-01 01:00:00'),
                                        pd.Timestamp('2001-01-01')])


def test_edges_load_t_step_no_repeat(edges):
    
    edges._load_t_step(-1)
    edges._load_t_step(1)
    
    assert len(edges._frame) == (4 * 19 + 5 * 18) * 7
    assert len(edges._t_steps) == 1


def test_edges_extract_sigma_no_geom(edges):
    
    gdf = edges.extract_sigma(-1, -0.5)
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 166
    assert gdf.columns.to_list() == ["geometry", "u1", '$k$', "n0", "n1"]
    assert set(gdf["geometry"].apply(lambda x: x.geom_type)) == \
                                                        set(['LineString'])
    
    assert gdf["u1"].min() > -1
    assert gdf["u1"].max() < 1
    assert gdf["$k$"].min() > 0.0035
    assert gdf["$k$"].max() < 0.0049
    assert set(gdf["n0"]) == set([0., -1., 1.])
    assert set(gdf["n1"]) == set([0., -1., 1.])


def test_edges_extract_sigma_line(edges):
    
    centreline = LineString(((0, 3), (18, 3)))
    gdf = edges.extract_sigma(-1, -0.5, centreline)
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 19
    assert gdf.columns.to_list() == ["geometry", "u1", '$k$']
    assert gdf["u1"].min() > -0.9
    assert gdf["u1"].max() < 0.9
    assert gdf["$k$"].min() > 0.0035
    assert gdf["$k$"].max() < 0.0049
    assert set(gdf["geometry"].apply(lambda x: x.geom_type)) == \
                                                        set(['Point'])
    
    wkt = gdf["geometry"].apply(lambda geom: geom.wkt)
    assert len(set(wkt)) == 19


def test_edges_extract_sigma_extrapolate_forward(edges):
    gdf = edges.extract_sigma(-1, 0)
    assert gdf["u1"].min() > -0.9
    assert gdf["u1"].max() < 0.9


def test_edges_extract_sigma_extrapolate_backward(edges):
    gdf = edges.extract_sigma(-1, -1)
    assert gdf["u1"].min() > -0.6
    assert gdf["u1"].max() < 0.61
