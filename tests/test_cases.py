# -*- coding: utf-8 -*-

from dataclasses import replace

import pytest

from snl_d3d_cec_verify.cases import CaseStudy, MycekStudy


@pytest.fixture
def casedef():
    return {"dx": (1, 2, 3, 4),
            "dy": (1, 2, 3, 4),
            "sigma": (1, 2, 3, 4)}


@pytest.fixture
def cases(casedef):
    return CaseStudy(**casedef)


def test_casestudy_fields():
    assert CaseStudy.fields == ['dx',
                                'dy',
                                'sigma',
                                'x0',
                                'x1',
                                'y0',
                                'y1',
                                'bed_level',
                                'dt_max',
                                'dt_init',
                                'turb_pos_x',
                                'turb_pos_y',
                                'turb_pos_z',
                                'discharge',
                                'bed_roughness',
                                'horizontal_eddy_viscosity',
                                'horizontal_eddy_diffusivity',
                                'vertical_eddy_viscosity',
                                'vertical_eddy_diffusivity',
                                'simulate_turbines',
                                'turbine_turbulence_model',
                                'beta_p',
                                'beta_d',
                                'c_epp',
                                'c_epd',
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
                            -2,
                            1,
                            1,
                            6,
                            3,
                            -1,
                            6.0574,
                            0.023,
                            1e-06,
                            1e-06,
                            1e-06,
                            1e-06,
                            True,
                            'delft',
                            1.,
                            1.84,
                            0.77,
                            0.13,
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


def test_casestudy_to_from_yaml(tmp_path, cases):
    
    d = tmp_path / "mock"
    d.mkdir()
    p = d / "test.yaml"
    cases.to_yaml(p)
    
    assert len(list(d.iterdir())) == 1
    
    test = CaseStudy.from_yaml(p)
    
    assert isinstance(test, CaseStudy)
    assert id(test) != id(cases)
    assert test == cases


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


def test_casestudy_not_eq_other(cases):
    assert cases != {"a": 1}


def test_casestudy_not_eq_scalar(cases):
    test = replace(cases, simulate_turbines=False)
    assert cases != test


def test_casestudy_eq_sequence(cases):
    test = replace(cases, dx=(2, 3, 4, 5))
    assert cases != test


def test_casestudy_isequal_ignore_fields(cases):
    ignore_fields = {"stats_interval": 1,
                     "restart_interval": 2}
    test = replace(cases, **ignore_fields)
    assert not cases.is_equal(test)
    assert cases.is_equal(test, ignore_fields)


@pytest.mark.parametrize("variable", ["x0", "x1", "y0", "y1", "bed_level"])
def test_mycekstudy_variables_error(variable):
    
    input_dict = {"dx": (1, 2, 3),
                  "dy": (2, 3, 4),
                  variable: 1}
    
    # Won't throw with CaseStudy but does with MycekStudy
    CaseStudy(**input_dict)
    
    with pytest.raises(TypeError) as excinfo:
        MycekStudy(**input_dict)
    
    assert variable in str(excinfo)


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


@pytest.fixture
def mycekcases(casedef):
    return MycekStudy(**casedef)


def test_mycekstudy_to_from_yaml(tmp_path, mycekcases):
    
    d = tmp_path / "mock"
    d.mkdir()
    p = d / "test.yaml"
    mycekcases.to_yaml(p)
    
    assert len(list(d.iterdir())) == 1
    
    test = MycekStudy.from_yaml(p)
    
    assert isinstance(test, MycekStudy)
    assert id(test) != id(cases)
    assert test == mycekcases


def test_casestudy_mycekstudy_equality(cases, mycekcases):
    assert cases == mycekcases
