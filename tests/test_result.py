# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import pytest

from snl_d3d_cec_verify import MycekStudy
from snl_d3d_cec_verify.result import (_FMModelResults,
                                       _StructuredModelResults,
                                       Result,
                                       Transect,
                                       Validate,
                                       get_reset_origin,
                                       get_normalised_dims,
                                       get_normalised_data,
                                       get_normalised_data_deficit,
                                       _get_axes_coords)
from snl_d3d_cec_verify.result.edges import Edges
from snl_d3d_cec_verify.result.faces import Faces, _FMFaces, _StructuredFaces


@pytest.fixture
def fmresult(data_dir):
    return _FMModelResults(data_dir)


def test_fmresult_path(data_dir, fmresult):
    expected = data_dir / "output" / "FlowFM_map.nc"
    assert fmresult.path == expected


def test_fmresult_x_lim(fmresult):
    x_low, x_high = fmresult.x_lim
    assert np.isclose(x_low, 0)
    assert np.isclose(x_high, 18)


def test_fmresult_y_lim(fmresult):
    y_low, y_high = fmresult.y_lim
    assert np.isclose(y_low, 1)
    assert np.isclose(y_high, 5)


def test_fmresult_times(fmresult):
    times = fmresult.times
    assert len(times) == 2
    assert times[0] == pd.Timestamp('2001-01-01')


def test_fmresult_edges(fmresult):
    assert isinstance(fmresult.edges, Edges)


def test_fmresult_faces(fmresult):
    assert isinstance(fmresult.faces, _FMFaces)


@pytest.fixture
def fmresultnone(tmp_path):
    return _FMModelResults(tmp_path)


def test_fmresultnone_path(fmresultnone):
    assert fmresultnone.path is None


def test_fmresultnone_x_lim(fmresultnone):
    assert fmresultnone.x_lim is None


def test_fmresultnone_y_lim(fmresultnone):
    assert fmresultnone.y_lim is None


def test_fmresultnone_times(fmresultnone):
    assert fmresultnone.times is None


def test_fmresultnone_edges(fmresultnone):
    assert fmresultnone.edges is None


def test_fmresultnone_faces(fmresultnone):
    assert fmresultnone.faces is None


@pytest.fixture
def structuredresult(data_dir):
    return _StructuredModelResults(data_dir)


def test_structuredresult_path(data_dir, structuredresult):
    expected = data_dir / "output" / "trim-D3D.nc"
    assert structuredresult.path == expected


def test_structuredresult_x_lim(structuredresult):
    x_low, x_high = structuredresult.x_lim
    assert np.isclose(x_low, 0)
    assert np.isclose(x_high, 18)


def test_structuredresult_y_lim(structuredresult):
    y_low, y_high = structuredresult.y_lim
    assert np.isclose(y_low, 1)
    assert np.isclose(y_high, 5)


def test_structuredresult_times(structuredresult):
    times = structuredresult.times
    assert len(times) == 2
    assert times[0] == pd.Timestamp('2001-01-01')


def test_structuredresult_edges(structuredresult):
    assert structuredresult.edges is None


def test_structuredresult_faces(structuredresult):
    assert isinstance(structuredresult.faces, _StructuredFaces)


@pytest.fixture
def structuredresultnone(tmp_path):
    return _StructuredModelResults(tmp_path)


def test_structuredresultnone_path(structuredresultnone):
    assert structuredresultnone.path is None


def test_structuredresultnone_x_lim(structuredresultnone):
    assert structuredresultnone.x_lim is None


def test_structuredresultnone_y_lim(structuredresultnone):
    assert structuredresultnone.y_lim is None


def test_structuredresultnone_times(structuredresultnone):
    assert structuredresultnone.times is None


def test_structuredresultnone_faces(structuredresultnone):
    assert structuredresultnone.faces is None


def test_Result_missing_files(tmp_path):
    
    with pytest.raises(FileNotFoundError) as excinfo:
        Result(tmp_path)
    
    assert "No valid model result files detected" in str(excinfo)


def test_Result_FM(data_dir):
    test = Result(data_dir)
    assert isinstance(test._faces, _FMFaces)


def test_Result_structured(mocker, data_dir):
    
    mocker.patch('snl_d3d_cec_verify.result._FMModelResults.is_model',
                 return_value=False)
    test = Result(data_dir)
    
    assert isinstance(test._faces, _StructuredFaces)


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
    assert "Result" in repr(result)
    assert repr(data_dir) in repr(result)


def test_transect_xy_length_mismatch():
    
    with pytest.raises(ValueError) as excinfo:
        Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1])
    
    assert "Length of x and y must match" in str(excinfo)


def test_transect_data_length_mismatch():
    
    with pytest.raises(ValueError) as excinfo:
        Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1], data=[2])
    
    assert "Length of data must match x and y" in str(excinfo)


@pytest.mark.parametrize("other, expected", [
                    (1, False),
                    (Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1]), True),
                    (Transect(id=0, z=0, x=[1, 2, 3], y=[1, 1, 1]), False),
                    (Transect(id=0, z=1, x=[0, 2, 3], y=[1, 1, 1]), False),
                    (Transect(id=0, z=1, x=[1, 2, 3], y=[0, 1, 1]), False),
                    (Transect(id=0,
                              z=1,
                              x=[1, 2, 3],
                              y=[1, 1, 1],
                              data=[0, 0, 0]), False)])
def test_transect_eq(other, expected):
    test = Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1])
    assert (test == other) is expected


@pytest.mark.parametrize("other, expected", [
    (Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1], data=[0, 0, 0]), True),
    (Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1], data=[1, 0, 0]), False)])
def test_transect_eq_data(other, expected):
    test = Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1], data=[0, 0, 0])
    assert (test == other) is expected


@pytest.mark.parametrize("other, expected", [
    (Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1], name="mock"), True),
    (Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1], name="not mock"), False),
    (Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1]), False)])
def test_transect_eq_name(other, expected):
    test = Transect(id=0, z=1, x=[1, 2, 3], y=[1, 1, 1], name="mock")
    assert (test == other) is expected


@pytest.mark.parametrize("other, expected", [
        (Transect(id=0,
                  z=1,
                  x=[1, 2, 3],
                  y=[1, 1, 1],
                  attrs={"mock": "mock"}), True),
        (Transect(id=0,
                  z=1,
                  x=[1, 2, 3],
                  y=[1, 1, 1],
                  attrs={"mock": "not mock"}), False),
        (Transect(id=0,
                  z=1,
                  x=[1, 2, 3],
                  y=[1, 1, 1],
                  attrs={"not mock": "mock"}), False),
        (Transect(id=0,
                  z=1, x=[1, 2, 3], y=[1, 1, 1]), False)])
def test_transect_eq_attrs(other, expected):
    test = Transect(id=0,
                    z=1,
                    x=[1, 2, 3],
                    y=[1, 1, 1],
                    attrs={"mock": "mock"})
    assert (test == other) is expected


def test_transect_from_csv(tmp_path, mocker):
    
    csv = ("x,y,z\n"
           "7,3,0\n"
           "8,3,0\n"
           "9,3,0\n")
    
    d = tmp_path / "mock"
    d.mkdir()
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    test = Transect.from_csv(d, 0, name="mock")
    expected = Transect(id=0,
                        z=0,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        name="mock",
                        attrs={"path": str(d.resolve())})
    
    assert test == expected


def test_transect_from_csv_attrs(tmp_path, mocker):
    
    csv = ("x,y,z\n"
           "7,3,0\n"
           "8,3,0\n"
           "9,3,0\n")
    
    d = tmp_path / "mock"
    d.mkdir()
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    test = Transect.from_csv(d,
                             0,
                             name="mock",
                             attrs={"mock": "mock",
                                    "path": "mock"})
    expected = Transect(id=0,
                        z=0,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        name="mock",
                        attrs={"path": str(d.resolve()),
                               "mock": "mock"})
    
    assert test == expected


def test_transect_from_csv_translation(tmp_path, mocker):
    
    csv = ("x,y,z\n"
           "1,1,1\n"
           "2,1,1\n"
           "3,1,1\n")
    
    d = tmp_path / "mock"
    d.mkdir()
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    test = Transect.from_csv(d, 0, translation=(6, 2, -1))
    expected = Transect(id=0,
                        z=0,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        attrs={"path": str(d.resolve())})
    
    assert test == expected


def test_transect_from_csv_with_data(tmp_path, mocker):
    
    csv = ("x,y,z,data\n"
           "7,3,0,1\n"
           "8,3,0,2\n"
           "9,3,0,3\n")
    
    d = tmp_path / "mock"
    d.mkdir()
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    test = Transect.from_csv(d, 0)
    expected = Transect(id=0,
                        z=0,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        data=[1, 2, 3],
                        attrs={"path": str(d.resolve())})
    
    assert test == expected


def test_transect_from_csv_multi_z_error(tmp_path, mocker):
    
    csv = ("x,y,z\n"
           "7,3,0\n"
           "8,3,1\n"
           "9,3,1\n")
    
    d = tmp_path / "mock"
    d.mkdir()
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=csv))
    
    with pytest.raises(ValueError) as excinfo:
        Transect.from_csv(d, 0)
    
    assert "only supports fixed z-value" in str(excinfo)


def test_transect_from_yaml(tmp_path, mocker):
    
    text = ("id: 0\n"
            "z: -1.0\n"
            "x: [7, 8, 9]\n"
            "y: [3, 3, 3]\n")
     
    d = tmp_path / "mock"
    d.mkdir()
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                 mocker.mock_open(read_data=text))
    
    test = Transect.from_yaml(d)
    expected = Transect(id=0,
                        z=-1,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        attrs={"path": str(d.resolve())})
    
    assert test == expected


def test_transect_from_yaml_optional(tmp_path, mocker):
    
    text = ("id: 0\n"
            "z: -1.0\n"
            "x: [7, 8, 9]\n"
            "y: [3, 3, 3]\n"
            "data: [1, 2, 3]\n"
            "name: $\\gamma_0$\n"
            "attrs:\n"
            "    mock: mock\n"
            "    path: not mock\n")
    
    d = tmp_path / "mock"
    d.mkdir()
    
    mocker.patch('snl_d3d_cec_verify.result.open',
                  mocker.mock_open(read_data=text))
    
    test = Transect.from_yaml(d)
    expected = Transect(id=0,
                        z=-1,
                        x=[7, 8, 9],
                        y=[3, 3, 3],
                        data=[1, 2, 3],
                        name="$\\gamma_0$",
                        attrs={"path": str(d.resolve()),
                               "mock": "mock"})
    
    assert test == expected

@pytest.fixture
def transect():
    return Transect(id=0,
                    z=1,
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
    assert result["value"] == expected["z"]
    assert (result["x"] == expected["x"]).all()
    assert (result["y"] == expected["y"]).all()


def test_trasect_extract(faces, transect):
    faces.extract_z(-1, **transect)


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
    
    transect = Transect(id=0,
                        z=1,
                        x=[1, 2, 3],
                        y=[1, 1, 1])
    result = transect.to_xarray()
    expected = np.zeros(3) * np.nan
    
    assert np.allclose(result.values, expected, equal_nan=True)


def test_validate_not_directory(tmp_path):
    
    p = tmp_path / "hello.txt"
    p.write_text("hello")
    
    with pytest.raises(FileNotFoundError) as excinfo:
        Validate(data_dir=p)
    
    assert "not a directory" in str(excinfo)


def test_validate_empty(tmp_path):
    test = Validate(data_dir=tmp_path)
    assert repr(test) == "Validate()"


def test_validate_id_clash(data_dir):
    
    transects_path = data_dir / "transects_bad"
    
    with pytest.raises(RuntimeError) as excinfo:
        Validate(data_dir=transects_path)
    
    assert "Transect ID '0'" in str(excinfo)
    assert "is already used" in str(excinfo)


def test_validate_mycek():
    test = Validate()
    assert len(test) >= 0


@pytest.fixture
def validate(data_dir):
    case = MycekStudy()
    transects_path = data_dir / "transects"
    return Validate(case, transects_path)


def test_validate_repr(validate):
    assert repr(validate) == ("Validate(0: mock 1\n"
                              "         1: mock 2)")


def test_validate_get_item(validate):
    
    transect = validate[0]
    expected = Transect(id=0,
                        z=-1,
                        x=[7, 8, 9],
                        y=[4, 4, 4],
                        data=[0, 0, 1],
                        attrs={"description": "mock 1",
                               "path": transect.attrs["path"]})
    
    assert transect == expected


def test_validate_iterate(validate):
    test = [i for i, _ in enumerate(validate)]
    expected = [0, 1]
    assert test == expected


def test_get_reset_origin(dataarray):
    
    result = get_reset_origin(dataarray, (1, 1, 1))
    
    assert result["$z$"] == 0
    assert np.isclose(result["$x$"].values, [0, 1, 2]).all()
    assert np.isclose(result["$y$"].values, [0, 0, 0]).all()


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
    assert np.isclose(result.values, [0, 0, 2]).all()


def test_get_normalised_data_latex():
    
    transect = Transect(id=0,
                        z=1,
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


@pytest.mark.parametrize("coords, missing", [
                            (["x", "y"], "z"),
                            (["x", "z"], "y"),
                            (["y", "z"], "x")])
def test_get_axes_coords_missing(coords, missing):
    
    with pytest.raises(KeyError) as excinfo:
        _get_axes_coords(coords)
    
    assert missing in str(excinfo)
