# -*- coding: utf-8 -*-

import math

import numpy as np
import pytest

from snl_d3d_cec_verify.grid.structured import make_eta_x, make_eta_y


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
