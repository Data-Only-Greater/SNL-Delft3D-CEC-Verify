# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import pytest

from snl_d3d_cec_verify.result import (get_x_lim,
                                       get_y_lim,
                                       get_step_times,
                                       Result)
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
