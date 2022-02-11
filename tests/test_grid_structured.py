# -*- coding: utf-8 -*-

import math

import numpy as np
import pytest

from snl_d3d_cec_verify.grid.structured import (write_rectangle,
                                                make_header,
                                                make_eta_x,
                                                make_eta_y)



@pytest.mark.parametrize("x0, x1, y0, y1", [
    (0, 18, 1, 5),
    (-10, 0, -5, 5),
    (0, 1, 5, 10),
    (-10, -5, -10, -5)])
def test_write_rectangle(tmp_path, x0, x1, y0, y1):
    
    write_rectangle(tmp_path, 1, 1, x0, x1, y0, y1)
    files = list(x for x in tmp_path.iterdir() if x.is_file())
    
    assert len(files) == 1
    
    grd_file = files[0]
    
    assert grd_file.name == "D3D.grd"
    
    with open(grd_file, "r") as f:
        lines = f.readlines()
    
    rows = 2 * math.ceil((x1 - x0 + 1) / 5) * (y1 - y0 + 1) + 8
    
    assert len(lines) == rows


def test_make_header():
    
    x = [0, 1, 2, 3, 4, 5, 6]
    y = [0, 1]
    
    observed = make_header(x, y)
    filtered = [v for v in observed if v[0] != "*"]
    
    assert len(filtered) == 4
    assert "Coordinate System" in filtered[0]
    assert filtered[0].split()[2] == "="
    assert filtered[0].split()[3] in ["Cartesian", "Spherical"]
    assert "Missing Value" in filtered[1]
    assert filtered[1].split()[2] == "="
    assert filtered[1].split()[3] == "-9.99999000000000024E+02"
    assert len(filtered[2].split()) == 2
    assert int(filtered[2].split()[0]) == len(x)
    assert int(filtered[2].split()[1]) == len(y)
    assert len(filtered[3].split()) == 3
    assert all([v.isdigit() for v in filtered[3].split()])


@pytest.mark.parametrize("x, y", [
    ([0, 1, 2, 3, 4, 5, 6], [0, 1]),
    ([0, 1, 2, 3], [0, 1]),
    ([0], [0, 1]),
    ([0, 1, 2, 3, 4, 5, 6], [0]),
    ([0, 1, 2, 3], [0])])
def test_make_eta_x(x, y):
    
    observed = make_eta_x(x, y)
    rows = math.ceil(len(x) / 5)
    
    assert len(observed) == len(y) * rows
    
    # Test the labels
    for i in range(len(y)):
        
        base_index = i * rows
        label, value = observed[base_index].split()[:2]
        
        assert label == "ETA="
        assert int(value) == i + 1
    
    # Test that x was recreated properly
    for i in range(len(y)):
        
        base_index = i * rows
        nums = [float(v) for v in observed[base_index].split()[2:]]
        
        for j in range(base_index + 1, (i + 1) * rows):
            nums += [float(v) for v in observed[j].split()]
        
        assert np.isclose(nums, x).all()


@pytest.mark.parametrize("x, y", [
    ([0, 1, 2, 3, 4, 5, 6], [0, 1]),
    ([0, 1, 2, 3], [0, 1]),
    ([0], [0, 1]),
    ([0, 1, 2, 3, 4, 5, 6], [0]),
    ([0, 1, 2, 3], [0])])
def test_make_eta_y(x, y):
    
    observed = make_eta_y(x, y)
    rows = math.ceil(len(x) / 5)
    
    assert len(observed) == len(y) * rows
    
    # Test the labels
    for i in range(len(y)):
        
        base_index = i * rows
        label, value = observed[base_index].split()[:2]
        
        assert label == "ETA="
        assert int(value) == i + 1
    
    # Test that y was recreated properly
    for i in range(len(y)):
        
        base_index = i * rows
        nums = [float(v) for v in observed[base_index].split()[2:]]
        
        for j in range(base_index + 1, (i + 1) * rows):
            nums += [float(v) for v in observed[j].split()]
        
        expected = [y[i]] * len(nums)
        
        assert np.isclose(nums, expected).all()
