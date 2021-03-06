# -*- coding: utf-8 -*-

import pytest

from snl_d3d_cec_verify.result.base import _TimeStepResolver


@pytest.mark.parametrize("index, expected", [
                                (-3, 0),
                                (-2, 1),
                                (-1, 2),
                                ( 0, 0),
                                ( 1, 1),
                                ( 2, 2)])
def test_TimeStepResolver_resolve_t_step(index, expected):
    test = _TimeStepResolver("mock", 3)
    assert test._resolve_t_step(index) == expected


@pytest.mark.parametrize("index", [-4, 3])
def test_TimeStepResolver_resolve_t_step_raises(index):
    
    test = _TimeStepResolver("mock", 3)
    
    with pytest.raises(IndexError) as excinfo:
        test._resolve_t_step(index)
    
    assert "out of range" in str(excinfo)
