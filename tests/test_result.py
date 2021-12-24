# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import pytest

from snl_d3d_cec_verify.result import (get_x_lim,
                                       get_y_lim,
                                       get_step_times,
                                       Result,
                                       Transect,
                                       get_normalised_dims,
                                       get_normalised_data,
                                       get_normalised_data_deficit)
from snl_d3d_cec_verify.result.edges import Edges
from snl_d3d_cec_verify.result.faces import Faces


def test_get_x_lim(data_dir):
    
    map_path = data_dir / "output" / "FlowFM_map.nc"
    x_low, x_high = get_x_lim(map_path)
    
    assert np.isclose(x_low, 0)
    assert np.isclose(x_high, 18)


def test_get_y_lim(data_dir):
    
    map_path = data_dir / "output" / "FlowFM_map.nc"
    y_low, y_high = get_y_lim(map_path)
    
    assert np.isclose(y_low, 1)
    assert np.isclose(y_high, 5)


def test_get_step_times(data_dir):
    
    map_path = data_dir / "output" / "FlowFM_map.nc"
    times = get_step_times(map_path)
    
    assert len(times) == 2
    assert times[0] == pd.Timestamp('2001-01-01')


@pytest.fixture
def result(data_dir):
    return Result(data_dir)


def test_result_x_lim(result):
    assert np.isclose(result.x_lim, [0, 18]).all()


def test_result_y_lim(result):
    assert np.isclose(result.y_lim, [1, 5]).all()


def test_result_times(result):
    assert result.times[0] == pd.Timestamp('2001-01-01')


def test_result_edges(result):
    assert isinstance(result.edges, Edges)


def test_result_faces(result):
    assert isinstance(result.faces, Faces)


def test_result__repr__(result, data_dir):
    map_path = data_dir / "output" / "FlowFM_map.nc"
    assert "Result" in repr(result)
    assert repr(map_path) in repr(result)


def test_transect_xy_length_mismatch():
    
    with pytest.raises(ValueError) as excinfo:
        Transect(z=1, x=[1, 2, 3], y=[1, 1])
    
    assert "Length of x and y must match" in str(excinfo)


def test_transect_data_length_mismatch():
    
    with pytest.raises(ValueError) as excinfo:
        Transect(z=1, x=[1, 2, 3], y=[1, 1, 1], data=[2])
    
    assert "Length of data must match x and y" in str(excinfo)


@pytest.mark.parametrize("other, expected", [
                    (1, False),
                    (Transect(z=1, x=[1, 2, 3], y=[1, 1, 1]), True),
                    (Transect(z=0, x=[1, 2, 3], y=[1, 1, 1]), False),
                    (Transect(z=1, x=[0, 2, 3], y=[1, 1, 1]), False),
                    (Transect(z=1, x=[1, 2, 3], y=[0, 1, 1]), False),
                    (Transect(z=1,
                              x=[1, 2, 3],
                              y=[1, 1, 1],
                              data=[0, 0, 0]), False)])
def test_transect_eq(other, expected):
    test = Transect(z=1, x=[1, 2, 3], y=[1, 1, 1])
    assert (test == other) is expected


@pytest.mark.parametrize("other, expected", [
        (Transect(z=1, x=[1, 2, 3], y=[1, 1, 1], data=[0, 0, 0]), True),
        (Transect(z=1, x=[1, 2, 3], y=[1, 1, 1], data=[1, 0, 0]), False)])
def test_transect_eq_data(other, expected):
    test = Transect(z=1, x=[1, 2, 3], y=[1, 1, 1], data=[0, 0, 0])
    assert (test == other) is expected


@pytest.mark.parametrize("other, expected", [
        (Transect(z=1, x=[1, 2, 3], y=[1, 1, 1], name="mock"), True),
        (Transect(z=1, x=[1, 2, 3], y=[1, 1, 1], name="not mock"), False),
        (Transect(z=1, x=[1, 2, 3], y=[1, 1, 1]), False)])
def test_transect_eq_name(other, expected):
    test = Transect(z=1, x=[1, 2, 3], y=[1, 1, 1], name="mock")
    assert (test == other) is expected


@pytest.mark.parametrize("other, expected", [
        (Transect(z=1,
                  x=[1, 2, 3],
                  y=[1, 1, 1],
                  attrs={"mock": "mock"}), True),
        (Transect(z=1,
                  x=[1, 2, 3],
                  y=[1, 1, 1],
                  attrs={"mock": "not mock"}), False),
        (Transect(z=1,
                  x=[1, 2, 3],
                  y=[1, 1, 1],
                  attrs={"not mock": "mock"}), False),
        (Transect(z=1, x=[1, 2, 3], y=[1, 1, 1]), False)])
def test_transect_eq_attrs(other, expected):
    test = Transect(z=1, x=[1, 2, 3], y=[1, 1, 1], attrs={"mock": "mock"})
    assert (test == other) is expected


def test_transect_from_csv(mocker):
    
    csv = ("x,y,z\n"
           "7,3,0\n"
           "8,3,0\n"
           "9,3,0\n")
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    test = Transect.from_csv("mock", name="mock")
    expected = Transect(z=0,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        name="mock",
                        attrs={"path": "mock"})
    
    assert test == expected


def test_transect_from_csv_attrs(mocker):
    
    csv = ("x,y,z\n"
           "7,3,0\n"
           "8,3,0\n"
           "9,3,0\n")
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    test = Transect.from_csv("mock",
                             name="mock",
                             attrs={"mock": "mock",
                                    "path": "not mock"})
    expected = Transect(z=0,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        name="mock",
                        attrs={"path": "mock",
                               "mock": "mock"})
    
    assert test == expected


def test_transect_from_csv_translation(mocker):
    
    csv = ("x,y,z\n"
           "1,1,1\n"
           "2,1,1\n"
           "3,1,1\n")
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    test = Transect.from_csv("mock", translation=(6, 2, -1))
    expected = Transect(z=0, x=[7, 8, 9], y=[3, 3, 3], attrs={"path": "mock"})
    
    assert test == expected


def test_transect_from_csv_with_data(mocker):
    
    csv = ("x,y,z,data\n"
           "7,3,0,1\n"
           "8,3,0,2\n"
           "9,3,0,3\n")
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    test = Transect.from_csv("mock")
    expected = Transect(z=0,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        data=[1, 2, 3],
                        attrs={"path": "mock"})
    
    assert test == expected


def test_transect_from_csv_multi_z_error(mocker):
    
    csv = ("x,y,z\n"
           "7,3,0\n"
           "8,3,1\n"
           "9,3,1\n")
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    with pytest.raises(ValueError) as excinfo:
        Transect.from_csv("mock")
    
    assert "only supports fixed z-value" in str(excinfo)


def test_transect_from_yaml(mocker):
    
    text = ("z: -1.0\n"
            "x: [7, 8, 9]\n"
            "y: [3, 3, 3]\n")
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=text))
    
    test = Transect.from_yaml("mock")
    expected = Transect(z=-1,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        attrs={"path": "mock"})
    
    assert test == expected


def test_transect_from_yaml_optional(mocker):
    
    text = ("z: -1.0\n"
            "x: [7, 8, 9]\n"
            "y: [3, 3, 3]\n"
            "data: [1, 2, 3]\n"
            "name: $\\gamma_0$\n"
            "attrs:\n"
            "    mock: mock\n"
            "    path: not mock\n")
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                  mocker.mock_open(read_data=text))
    
    test = Transect.from_yaml("mock")
    expected = Transect(z=-1,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        data=[1, 2, 3],
                        name="$\\gamma_0$",
                        attrs={"path": "mock",
                               "mock": "mock"})
    
    assert test == expected

@pytest.fixture
def transect():
    return Transect(z=1,
                    x=[1, 2, 3],
                    y=[1, 1, 1],
                    data=[0, 0, 1],
                    name="mock")


def test_trasect_unpacking(transect):
    
    result = dict(**transect)
    expected = {"z": 1,
                "x": np.array([1, 2, 3]),
                "y": np.array([1, 1, 1])}
    
    assert "data" not in result
    assert result["kz"] == expected["z"]
    assert (result["x"] == expected["x"]).all()
    assert (result["y"] == expected["y"]).all()


@pytest.fixture
def dataarray(transect):
    return transect.to_xarray()


def test_trasect_to_xarray(dataarray, transect):
    assert dataarray.name == transect.name
    assert dataarray["$z$"] == transect.z
    assert (dataarray["$x$"] == transect.x).all()
    assert (dataarray["$y$"] == transect.y).all()
    assert (dataarray.values == transect.data).all()


def test_trasect_to_xarray_no_data():
    
    transect = Transect(z=1,
                        x=[1, 2, 3],
                        y=[1, 1, 1])
    result = transect.to_xarray()
    expected = np.zeros(3) * np.nan
    
    assert np.allclose(result.values, expected, equal_nan=True)


def test_get_normalised_dims(dataarray):
    
    result = get_normalised_dims(dataarray, 0.5)
    
    assert set(list(result.coords.keys())) == set(["$z^*$",
                                                   "$x^*$",
                                                   "$y^*$"])
    
    assert result["$z^*$"] == 2
    assert np.isclose(result["$x^*$"].values, [2, 4, 6]).all()
    assert np.isclose(result["$y^*$"].values, [2, 2, 2]).all()


def test_get_normalised_data(dataarray):
    
    result = get_normalised_data(dataarray, 0.5)
    
    assert result.name == "mock *"
    assert np.isclose(result.values, [0, 0, 0.5]).all()


def test_get_normalised_data_latex():
    
    transect = Transect(z=1,
                        x=[1, 2, 3],
                        y=[1, 1, 1],
                        data=[0, 0, 1],
                        name="$x$ mock")
    dataarray = transect.to_xarray()
    
    result = get_normalised_data(dataarray, 0.5)
    
    assert result.name == "$x^*$ mock"


@pytest.mark.parametrize("name", ["mock_zero", None])
def test_get_normalised_data_deficit(name, dataarray):
    
    result = get_normalised_data_deficit(dataarray, 2, name)
    
    assert result.name == name
    assert np.isclose(result.values, [100, 100, 50]).all()
