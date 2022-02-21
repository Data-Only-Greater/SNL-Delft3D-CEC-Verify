# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import xarray as xr
import pytest

from snl_d3d_cec_verify.cases import CaseStudy
from snl_d3d_cec_verify.result.faces import (_check_case_study,
                                             _faces_frame_to_slice,
                                             _faces_frame_to_depth,
                                             Faces,
                                             _map_to_faces_frame,
                                             _FMFaces,
                                             _trim_to_faces_frame,
                                             _StructuredFaces)


def test_check_case_study_error():
    
    case = CaseStudy(dx=[1, 2, 3])
    
    with pytest.raises(ValueError) as excinfo:
        _check_case_study(case)
    
    assert "case study must have length one" in str(excinfo)


@pytest.fixture
def faces_frame(data_dir):
    csv_path = data_dir / "output" / "faces_frame.csv"
    frame = pd.read_csv(csv_path, parse_dates=["time"])
    times = frame.time.unique()
    return frame[frame.time == times[-1]]


def test_faces_frame_to_slice_k(faces_frame):
    
    ts = pd.Timestamp("2001-01-01 01:00:00")
    k = 0
    ds = _faces_frame_to_slice(faces_frame, ts, k=k)
    
    assert isinstance(ds, xr.Dataset)
    
    assert len(ds["$x$"]) == 18
    assert len(ds["$y$"]) == 4
    
    assert np.isclose(ds["$x$"].min(), 0.5)
    assert np.isclose(ds["$x$"].max(), 17.5)
    assert np.isclose(ds["$y$"].min(), 1.5)
    assert np.isclose(ds["$y$"].max(), 4.5)
    
    assert ds.k.values.take(0) == k
    assert ds.time.values.take(0) == ts
    
    assert ds["$z$"].min() > -1.669
    assert ds["$z$"].max() < -1.666
    
    # Same bounds as the frame
    assert ds["$u$"].min() >= faces_frame["u"].min()
    assert ds["$u$"].max() <= faces_frame["u"].max()
    assert ds["$v$"].min() >= faces_frame["v"].min()
    assert ds["$v$"].max() <= faces_frame["v"].max()
    assert ds["$w$"].min() >= faces_frame["w"].min()
    assert ds["$w$"].max() <= faces_frame["w"].max()


def test_faces_frame_to_slice_z(faces_frame):
    
    ts = pd.Timestamp("2001-01-01 01:00:00")
    z = -1
    ds = _faces_frame_to_slice(faces_frame, ts, z=z)
    
    assert isinstance(ds, xr.Dataset)
    
    assert len(ds["$x$"]) == 18
    assert len(ds["$y$"]) == 4
    
    assert np.isclose(ds["$x$"].min(), 0.5)
    assert np.isclose(ds["$x$"].max(), 17.5)
    assert np.isclose(ds["$y$"].min(), 1.5)
    assert np.isclose(ds["$y$"].max(), 4.5)
    
    assert ds["$z$"].values.take(0) == z
    assert ds.time.values.take(0) == ts
    
    assert ds.k.min() > 1
    assert ds["$z$"].max() < 1.002
    
    # Same bounds as the frame
    assert ds["$u$"].min() >= faces_frame["u"].min()
    assert ds["$u$"].max() <= faces_frame["u"].max()
    assert ds["$v$"].min() >= faces_frame["v"].min()
    assert ds["$v$"].max() <= faces_frame["v"].max()
    assert ds["$w$"].min() >= faces_frame["w"].min()
    assert ds["$w$"].max() <= faces_frame["w"].max()


@pytest.mark.parametrize("k, z", [
                            ("mock", "mock"),
                            (None, None)])
def test_faces_frame_to_slice_k_z_error(k, z):
    
    with pytest.raises(RuntimeError) as excinfo:
        _faces_frame_to_slice("mock", "mock", k=k, z=z)
    
    assert "either k or z must be given" in str(excinfo)


def test_faces_frame_to_depth(faces_frame):
    
    ts = pd.Timestamp("2001-01-01 01:00:00")
    da = _faces_frame_to_depth(faces_frame, ts)
    
    assert isinstance(da, xr.DataArray)
    
    assert len(da["$x$"]) == 18
    assert len(da["$y$"]) == 4
    assert da.time.values.take(0) == ts
    
    # Same bounds as the frame
    assert da.min() >= faces_frame["depth"].min()
    assert da.max() <= faces_frame["depth"].max()


class MockFaces(Faces):
    def _get_faces_frame(self, t_step: int) -> pd.DataFrame:
        frame = pd.read_csv(self.nc_path, parse_dates=["time"])
        times = frame.time.unique()
        return frame[frame.time == times[t_step]]


@pytest.fixture
def faces(data_dir):
    csv_path = data_dir / "output" / "faces_frame.csv"
    return MockFaces(csv_path, 2, 18)


def test_faces_load_t_step_first(faces):
    
    t_step = -1
    expected_t_step = faces._resolve_t_step(t_step)
    faces._load_t_step(t_step)
    
    assert len(faces._frame) == 216
    assert expected_t_step in faces._t_steps
    assert faces._t_steps[expected_t_step] == \
                                        pd.Timestamp('2001-01-01 01:00:00')


def test_faces_load_t_step_second(faces):
    
    faces._load_t_step(-1)
    faces._load_t_step(0)
    
    assert len(faces._frame) == 216 * 2
    assert len(faces._t_steps) == 2
    assert set(faces._frame["time"]) == set([
                                        pd.Timestamp('2001-01-01 01:00:00'),
                                        pd.Timestamp('2001-01-01')])


def test_faces_load_t_step_no_repeat(faces):
    
    faces._load_t_step(-1)
    faces._load_t_step(1)
    
    assert len(faces._frame) == 216
    assert len(faces._t_steps) == 1


def test_faces_extract_depth(mocker, faces):
    mock = mocker.patch('snl_d3d_cec_verify.result.faces.'
                        '_faces_frame_to_depth')
    faces.extract_depth(-1)
    mock.assert_called()


def test_faces_extract_k(mocker, faces):
    mock = mocker.patch('snl_d3d_cec_verify.result.faces.'
                        '_faces_frame_to_slice')
    faces.extract_k(-1, 0)
    mock.assert_called()
    assert 'k' in mock.call_args.kwargs
    assert 'z' not in mock.call_args.kwargs


def test_faces_extract_k_interp(faces):
    
    t_step = -1
    k = 0
    x = 1
    y = 3
    
    ds = faces.extract_k(t_step, k, x, y)
    t_step = faces._resolve_t_step(t_step)
    ts = faces._t_steps[t_step]
    
    assert isinstance(ds, xr.Dataset)
    
    assert ds.k.values.take(0) == k
    assert ds.time.values.take(0) == ts
    assert ds["$x$"].values.take(0) == x
    assert ds["$y$"].values.take(0) == y
    assert np.isclose(ds["$z$"].values, -1.66857945)
    
    # Same bounds as the frame
    assert (faces._frame["u"].min() <= ds["$u$"].values.take(0) <=
                                                    faces._frame["u"].max())
    assert (faces._frame["v"].min() <= ds["$v$"].values.take(0) <=
                                                    faces._frame["v"].max())
    assert (faces._frame["w"].min() <= ds["$w$"].values.take(0) <=
                                                    faces._frame["w"].max())


def test_faces_extract_z(mocker, faces):
    mock = mocker.patch('snl_d3d_cec_verify.result.faces.'
                        '_faces_frame_to_slice')
    faces.extract_z(-1, -1)
    mock.assert_called()
    assert 'z' in mock.call_args.kwargs
    assert 'k' not in mock.call_args.kwargs


def test_faces_extract_z_interp(faces):
    
    t_step = -1
    z = -1
    x = 1
    y = 3
    
    ds = faces.extract_z(t_step, z, x, y)
    t_step = faces._resolve_t_step(t_step)
    ts = faces._t_steps[t_step]
    
    assert isinstance(ds, xr.Dataset)
    
    assert ds["$z$"].values.take(0) == z
    assert ds.time.values.take(0) == ts
    assert ds["$x$"].values.take(0) == x
    assert ds["$y$"].values.take(0) == y
    assert np.isclose(ds.k.values, 1.00171953)
    
    # Same bounds as the frame
    assert (faces._frame["u"].min() <= ds["$u$"].values.take(0) <=
                                                    faces._frame["u"].max())
    assert (faces._frame["v"].min() <= ds["$v$"].values.take(0) <=
                                                    faces._frame["v"].max())
    assert (faces._frame["w"].min() <= ds["$w$"].values.take(0) <=
                                                    faces._frame["w"].max())


@pytest.mark.parametrize("x, y", [
                            ("mock", None),
                            (None, "mock")])
def test_faces_extract_interp_error(faces, x, y):
    
    with pytest.raises(RuntimeError) as excinfo:
        faces.extract_z("mock", "mock", x, y)
    
    assert "x and y must both be set" in str(excinfo)


def test_faces_extract_turbine_z(mocker, faces):
    
    case = CaseStudy()
    offset_z = 0.5
    t_step = -1
    mock = mocker.patch.object(faces, 'extract_z')
    faces.extract_turbine_z(t_step, case, offset_z)
    
    mock.assert_called_with(t_step, case.turb_pos_z + offset_z)


def test_faces_extract_turbine_centreline(mocker, faces):
    
    case = CaseStudy()
    t_step = -1
    x_step = 0.5
    offset_x = 0.5
    offset_y = 0.5
    offset_z = 0.5
    mock = mocker.patch.object(faces, 'extract_z')
    faces.extract_turbine_centreline(t_step,
                                     case,
                                     x_step,
                                     offset_x,
                                     offset_y,
                                     offset_z)
    
    mock.assert_called()
    
    assert mock.call_args.args[0] == t_step
    assert mock.call_args.args[1] == case.turb_pos_z + offset_z
    
    x = mock.call_args.args[2]
    y = mock.call_args.args[3]
    
    assert x.min() == case.turb_pos_x + offset_x
    assert x.max() <= faces.xmax
    assert np.unique(np.diff(x)).take(0) == x_step
    assert set(y) == set([case.turb_pos_y + offset_y])


def test_faces_extract_turbine_centre(mocker, faces):
    
    case = CaseStudy()
    t_step = -1
    offset_x = 0.5
    offset_y = 0.5
    offset_z = 0.5
    mock = mocker.patch.object(faces, 'extract_z')
    faces.extract_turbine_centre(t_step,
                                 case,
                                 offset_x,
                                 offset_y,
                                 offset_z)
    
    mock.assert_called()
    
    assert mock.call_args.args[0] == t_step
    assert mock.call_args.args[1] == case.turb_pos_z + offset_z
    
    x = mock.call_args.args[2]
    y = mock.call_args.args[3]
    
    assert len(x) == 1
    assert len(y) == 1
    assert x[0] == case.turb_pos_x + offset_x
    assert y[0] == case.turb_pos_y + offset_y



def test_map_to_faces_frame(data_dir):
    
    map_path = data_dir / "output" / "FlowFM_map.nc"
    faces_frame = _map_to_faces_frame(map_path, -1)
    
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


def test_FMFaces(mocker):
    
    mock = mocker.patch('snl_d3d_cec_verify.result.faces._map_to_faces_frame',
                        autospec=True)
    
    path = "mock"
    tstep = 0
    
    test = _FMFaces(path, 2, 18)
    test._get_faces_frame(tstep)
    
    mock.assert_called_with(path, tstep)


def test_trim_to_faces_frame(data_dir):
    
    trim_path = data_dir / "output" / "trim-D3D.nc"
    faces_frame = _trim_to_faces_frame(trim_path, -1)
    
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
    assert faces_frame["depth"].max() < 2.005
    
    assert faces_frame["u"].min() > 0.6
    assert faces_frame["u"].max() < 0.9
    assert faces_frame["v"].min() > -1e-2
    assert faces_frame["v"].max() < 1e-2
    assert faces_frame["w"].min() > -0.03
    assert faces_frame["w"].max() < 0.02


def test_StructuredFaces(mocker):
    
    mock = mocker.patch('snl_d3d_cec_verify.result.faces._trim_to_faces_frame',
                        autospec=True)
    
    path = "mock"
    tstep = 0
    
    test = _StructuredFaces(path, 2, 18)
    test._get_faces_frame(tstep)
    
    mock.assert_called_with(path, tstep)
