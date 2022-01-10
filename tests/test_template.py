# -*- coding: utf-8 -*-

from pathlib import Path

import pytest

from snl_d3d_cec_verify.cases import CaseStudy
from snl_d3d_cec_verify.template import package_fm_template_path, Template


def test_package_fm_template_path():
    expected = Path("snl_d3d_cec_verify") / "templates" / "fm"
    result = package_fm_template_path()
    assert str(expected) in str(result)


def test_template_call(mocker):
    
    mock_copy = mocker.patch("snl_d3d_cec_verify.template.copy",
                             autospec=True)
    mock_write_gridfm_rectangle = mocker.patch(
                    "snl_d3d_cec_verify.template.write_gridfm_rectangle",
                    autospec=True)
    
    template_path = "mock_template"
    exist_ok = True
    case = CaseStudy()
    project_path = "mock_template"
    
    excluded_fields = ["dx", "dy"]
    expected_fields = [field for field in case.fields
                                           if field not in excluded_fields]
    expected_net_path = Path(project_path) / "input" / "FlowFM_net.nc"
    
    template = Template(template_path, exist_ok)
    template(case, project_path)
    
    mock_copy.assert_called()
    mock_copy_kwargs = mock_copy.call_args.kwargs
    
    assert set(mock_copy.call_args.args) == set([Path(template_path),
                                                 Path(project_path)])
    assert set(expected_fields) <= set(mock_copy_kwargs["data"])
    assert mock_copy_kwargs["exist_ok"] is exist_ok
    assert mock_copy_kwargs["data"]["horizontal_momentum_filter"] == 1
    
    mock_write_gridfm_rectangle.assert_called_with(expected_net_path,
                                                   case.dx,
                                                   case.dy)


@pytest.mark.parametrize("simulate_turbines", [True, False])
def test_template_fm_simulate_turbines(mocker, simulate_turbines):
    
    mocker.patch("snl_d3d_cec_verify.template.write_gridfm_rectangle",
                 autospec=True)
    mocker.patch("snl_d3d_cec_verify.copier._basic_copy",
                 autospec=True)
    mock_write = mocker.patch('snl_d3d_cec_verify.copier.open',
                              mocker.mock_open())
    
    case = CaseStudy(simulate_turbines=simulate_turbines)
    project_path = "mock_template"
    
    template = Template()
    template(case, project_path)
    
    open_args, _ = mock_write.call_args_list[1]
    
    assert open_args[0] == Path("mock_template/input/FlowFM.mdu")
    
    handle = mock_write()
    write_args, _ = handle.write.call_args_list[1]
    
    assert ("[Turbines]\n" in write_args[0]) is simulate_turbines


def test_template_call_too_many_cases():
    
    template = Template("mock_template")
    case = CaseStudy(dx=[1, 2])
    
    with pytest.raises(ValueError) as excinfo:
        template(case, "mock")
    
    assert "case study must have length one" in str(excinfo)
