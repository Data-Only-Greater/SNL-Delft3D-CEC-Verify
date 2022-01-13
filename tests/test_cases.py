# -*- coding: utf-8 -*-

import pytest

from snl_d3d_cec_verify.cases import CaseStudy, MycekStudy


@pytest.fixture
def cases():
    return CaseStudy(dx=(1, 2, 3, 4),
                     dy=(1, 2, 3, 4),
                     sigma=(1, 2, 3, 4))


def test_casestudy_fields():
    assert CaseStudy.fields == ['dx',
                                'dy',
                                'sigma',
                                'x0',
                                'x1',
                                'y0',
                                'y1',
                                'dt_max',
                                'dt_init',
                                'turb_pos_x',
                                'turb_pos_y',
                                'turb_pos_z',
                                'discharge',
                                'horizontal_eddy_viscosity',
                                'horizontal_eddy_diffusivity',
                                'vertical_eddy_viscosity',
                                'vertical_eddy_diffusivity',
                                'simulate_turbines',
                                'horizontal_momentum_filter',
                                'stats_interval',
                                'restart_interval']


def test_casestudy_unequal_inputs():
    
    with pytest.raises(ValueError) as excinfo:
        CaseStudy(dx=(1, 2, 3), dy=(1, 2, 3, 4))
    
    assert "non-equal lengths" in str(excinfo)


def test_casestudy_init(cases):
    assert len(cases) == 4


def test_casestudy_values(cases):
    assert cases.values == [(1, 2, 3, 4),
                            (1, 2, 3, 4),
                            (1, 2, 3, 4),
                            0,
                            18,
                            1,
                            5,
                            1,
                            1,
                            6,
                            3,
                            -1,
                            6.0574,
                            1e-06,
                            1e-06,
                            1e-06,
                            1e-06,
                            True,
                            True,
                            None,
                            0]


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_casestudy_get_case(cases, index):
    case = cases.get_case(index)
    assert len(case) == 1
    assert case.dx == index + 1
    assert case.dy == index + 1
    assert case.sigma == index + 1


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_casestudy_getitem(cases, index):
    case = cases[index]
    assert len(case) == 1
    assert case.dx == index + 1
    assert case.dy == index + 1
    assert case.sigma == index + 1


@pytest.mark.parametrize("index", [-5, 4])
def test_casestudy_get_case_out_of_bounds(cases, index):
    
    with pytest.raises(IndexError) as excinfo:
        cases.get_case(index)
    
    assert "index out of range" in str(excinfo)


def test_casestudy_get_case_single(cases):
    case = cases.get_case()
    test = case.get_case()
    
    assert len(test) == 1
    assert test.dx == case.dx
    assert test.dy == case.dy
    assert test.sigma == case.sigma
    assert test is not case


def test_casestudy_length_one_sequences():
    
    test = CaseStudy(dx=(1,),
                     dy=(1,),
                     sigma=(1,))
    
    assert len(test) == 1
    assert test.dx == 1
    assert test.dy == 1
    assert test.sigma == 1


@pytest.mark.parametrize("index", [-2, 1])
def test_casestudy_get_case_out_of_bounds_sigle(cases, index):
    
    case = cases.get_case(0)
    
    with pytest.raises(IndexError) as excinfo:
        case.get_case(index)
    
    assert "index out of range" in str(excinfo)


@pytest.mark.parametrize("axis", ["x", "y", "z"])
def test_mycekstudy_turb_pos_error(axis):
    
    input_dict = {"dx": (1, 2, 3),
                  "dy": (2, 3, 4),
                  f"turb_pos_{axis}": 1}
    
    # Won't throw with CaseStudy but does with MycekStudy
    CaseStudy(**input_dict)
    
    with pytest.raises(TypeError) as excinfo:
        MycekStudy(**input_dict)
    
    assert f"turb_pos_{axis}" in str(excinfo)
