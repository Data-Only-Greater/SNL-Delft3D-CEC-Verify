# -*- coding: utf-8 -*-

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import pytest

from snl_d3d_cec_verify.result.faces import (map_to_faces_frame,
                                             faces_frame_to_slice,
                                             faces_frame_to_depth)


@pytest.fixture
def data_dir():
    this_file = Path(__file__).resolve()
    return (this_file.parent / ".." / "test_data").resolve()


@pytest.fixture
def faces_frame(data_dir):
    map_path = data_dir / "output" / "FlowFM_map.nc"
    return map_to_faces_frame(map_path, -1)


def test_map_to_faces_frame(faces_frame):
    
    assert isinstance(faces_frame, pd.DataFrame)
    assert len(faces_frame) == 216
    assert faces_frame.columns.to_list() == ["x",
                                             "y",
                                             "z",
                                             "k",
                                             "time",
                                             "depth",
                                             "u",
                                             "v",
                                             "w"]
    
    assert np.isclose(faces_frame["x"].min(), 0.5)
    assert np.isclose(faces_frame["x"].max(), 17.5)
    assert np.isclose(faces_frame["y"].min(), 1.5)
    assert np.isclose(faces_frame["y"].max(), 4.5)
    assert -2 < faces_frame["z"].min() < -4 / 3
    assert -2 / 3 < faces_frame["z"].max() < 0
    
    assert set(faces_frame["k"]) == set([0, 1, 2])
    assert set(faces_frame["time"]) == set([
                                        pd.Timestamp('2001-01-01 01:00:00')])
    assert faces_frame["depth"].min() > 2
    assert faces_frame["depth"].max() < 2.003
    
    assert faces_frame["u"].min() > 0.6
    assert faces_frame["u"].max() < 0.9
    assert faces_frame["v"].min() > -1e-15
    assert faces_frame["v"].max() < 1e-15
    assert faces_frame["w"].min() > -0.02
    assert faces_frame["w"].max() < 0.02


def test_faces_frame_to_slice_k(faces_frame):
    
    ts = pd.Timestamp("2001-01-01 01:00:00")
    k = 0
    ds = faces_frame_to_slice(faces_frame, ts, k=k)
    
    assert isinstance(ds, xr.Dataset)
    
    assert len(ds.x) == 18
    assert len(ds.y) == 4
    
    assert np.isclose(ds.x.min(), 0.5)
    assert np.isclose(ds.x.max(), 17.5)
    assert np.isclose(ds.y.min(), 1.5)
    assert np.isclose(ds.y.max(), 4.5)
    
    assert ds.k.values.take(0) == k
    assert ds.time.values.take(0) == ts
    
    assert ds.z.min() > -1.669
    assert ds.z.max() < -1.666
    
    # Same bounds as the frame
    assert ds.u.min() >= faces_frame["u"].min()
    assert ds.u.max() <= faces_frame["u"].max()
    assert ds.v.min() >= faces_frame["v"].min()
    assert ds.v.max() <= faces_frame["v"].max()
    assert ds.w.min() >= faces_frame["w"].min()
    assert ds.w.max() <= faces_frame["w"].max()


def test_faces_frame_to_slice_z(faces_frame):
    
    ts = pd.Timestamp("2001-01-01 01:00:00")
    z = -1
    ds = faces_frame_to_slice(faces_frame, ts, z=z)
    
    assert isinstance(ds, xr.Dataset)
    
    assert len(ds.x) == 18
    assert len(ds.y) == 4
    
    assert np.isclose(ds.x.min(), 0.5)
    assert np.isclose(ds.x.max(), 17.5)
    assert np.isclose(ds.y.min(), 1.5)
    assert np.isclose(ds.y.max(), 4.5)
    
    assert ds.z.values.take(0) == z
    assert ds.time.values.take(0) == ts
    
    assert ds.k.min() > 1
    assert ds.z.max() < 1.002
    
    # Same bounds as the frame
    assert ds.u.min() >= faces_frame["u"].min()
    assert ds.u.max() <= faces_frame["u"].max()
    assert ds.v.min() >= faces_frame["v"].min()
    assert ds.v.max() <= faces_frame["v"].max()
    assert ds.w.min() >= faces_frame["w"].min()
    assert ds.w.max() <= faces_frame["w"].max()


@pytest.mark.parametrize("k, z", [
                            ("mock", "mock"),
                            (None, None)])
def test_faces_frame_to_slice_k_z_error(k, z):
    
    with pytest.raises(RuntimeError) as excinfo:
        faces_frame_to_slice("mock", "mock", k=k, z=z)
    
    assert "either k or z must be given" in str(excinfo)


def test_faces_frame_to_depth(faces_frame):
    
    ts = pd.Timestamp("2001-01-01 01:00:00")
    da = faces_frame_to_depth(faces_frame, ts)
    
    assert isinstance(da, xr.DataArray)
    
    assert len(da.x) == 18
    assert len(da.y) == 4
    assert da.time.values.take(0) == ts
    
    # Same bounds as the frame
    assert da.min() >= faces_frame["depth"].min()
    assert da.max() <= faces_frame["depth"].max()
