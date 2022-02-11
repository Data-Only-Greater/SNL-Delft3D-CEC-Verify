# -*- coding: utf-8 -*-

import numpy as np
import pytest

from snl_d3d_cec_verify.grid.shared import generate_grid_xy


@pytest.mark.parametrize("dx, dy, expected_shape", [
                            (1, 1, (3, 2)),
                            (0.9, 1, (4, 2)),
                            (1, 0.9, (3, 3)),
                            (0.9, 0.9, (4, 3))])
def test_generate_grid_xy(dx, dy, expected_shape):
    
    x0 = 0
    y0 = 0
    xsize = 2
    ysize = 1
    
    x, y = generate_grid_xy(x0, y0, xsize, ysize, dx, dy)
    
    assert np.isclose((x[0], y[0]), (x0, y0)).all()
    assert np.isclose((x[-1], y[-1]), (xsize, ysize)).all()
    assert np.isclose((len(x), len(y)), expected_shape).all()
    assert np.isclose(np.diff(x)[:-1], dx).all()
    assert np.isclose(np.diff(y)[:-1], dy).all()
