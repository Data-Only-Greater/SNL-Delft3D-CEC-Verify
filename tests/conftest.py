# -*- coding: utf-8 -*-

from pathlib import Path

import numpy as np
import pytest

from snl_d3d_cec_verify.result import Transect



def pytest_assertrepr_compare(op, left, right):
    
    if (isinstance(left, Transect) and
        isinstance(right, Transect) and
        op == "=="):
        
        comparison = ["Transect:"]
        get_comp_str = lambda name: \
            f"   {name}: {getattr(left, name)} == {getattr(right, name)}"
        
        if not left.z == right.z:
            comparison.append(get_comp_str("z"))
            
        if not np.isclose(left.x, right.x).all():
            comparison.append(get_comp_str("x"))
            
        if not np.isclose(left.y, right.y).all():
            comparison.append(get_comp_str("y"))
        
        none_check = sum([1 if x is None else 0 for x in
                                                  [left.data, right.data]])
        
        if none_check == 1:
            comparison.append(get_comp_str("data"))
        
        if none_check == 0:
            assert left.data is not None
            assert right.data is not None
            if not np.isclose(left.data, right.data).all():
                comparison.append(get_comp_str("data"))
        
        optionals = ("name", "attrs")
        
        for key in optionals:
            
            none_check = sum([1 if x is None else 0 for x in (left[key],
                                                              right[key])])
            
            if none_check == 1:
                comparison.append(get_comp_str(key))
                
            if none_check == 0 and left[key] != right[key]:
                comparison.append(get_comp_str(key))
        
        return comparison


@pytest.fixture
def data_dir():
    this_file = Path(__file__).resolve()
    return (this_file.parent / ".." / "test_data").resolve()
