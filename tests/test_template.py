# -*- coding: utf-8 -*-

import platform
from pathlib import Path
from datetime import datetime, timedelta
from importlib.metadata import version

import numpy as np
import pytest

from snl_d3d_cec_verify.cases import CaseStudy
from snl_d3d_cec_verify.template import (_FMTemplateExtras,
                                         _StructuredTemplateExtras,
                                         _package_template_path,
                                         Template)


@pytest.fixture
def fmextras():
    return _FMTemplateExtras()


@pytest.mark.parametrize("simulate_turbines", [True, False])
def test_FMTemplateExtras_data_hook(fmextras, simulate_turbines):
    case = CaseStudy(simulate_turbines=simulate_turbines)
    data = {}
    fmextras.data_hook(case, data)
    assert ("[Turbines]\n" in data["simulate_turbines"]) is simulate_turbines


def test_FMTemplateExtras_write_grid(mocker, fmextras):
    
    mock_write_fm_rectangle = mocker.patch(
                    "snl_d3d_cec_verify.template.write_fm_rectangle",
                    autospec=True)
    
    case = CaseStudy()
    project_path = "mock_template"
    expected_net_path = Path(project_path) / "input" / "FlowFM_net.nc"
    
    fmextras.write_grid(project_path,
                        case.dx,
                        case.dy,
                        case.x0,
                        case.x1,
                        case.y0,
                        case.y1)
    
    mock_write_fm_rectangle.assert_called_with(expected_net_path,
                                               case.dx,
                                               case.dy,
                                               case.x0,
                                               case.x1,
                                               case.y0,
                                               case.y1)


@pytest.fixture
def structuredextras():
    return _StructuredTemplateExtras()


def test_StructuredTemplateExtras_data_hook_no_turbines(structuredextras):
    
    case = CaseStudy(simulate_turbines=False)
    data = {}
    structuredextras.data_hook(case, data)
    
    assert data["version"] == f"{version('SNL-Delft3D-CEC-Verify')}"
    assert data["os"] == f"{platform.system()}"
    assert not data["simulate_turbines"]
    
    then = datetime.strptime(data["date"], '%Y-%m-%d, %H:%M:%S')
    now = datetime.now()
    
    assert now - then < timedelta(seconds=5)


def test_StructuredTemplateExtras_data_hook_turbines(mocker, structuredextras):
    
    turb_pos_x = 6
    turb_pos_y = 3
    
    x = np.array([turb_pos_x])
    y = np.array([turb_pos_y])
    
    mocker.patch("snl_d3d_cec_verify.template.generate_grid_xy",
                 return_value=(x, y),
                 autospec=True)
    
    case = CaseStudy(turb_pos_x=turb_pos_x, turb_pos_y=turb_pos_y)
    data = {"turb_pos_x": turb_pos_x,
            "turb_pos_y": turb_pos_y}
    structuredextras.data_hook(case, data)
    
    assert "Filtrb = #turbines.ini#" in data["simulate_turbines"]
    assert data["turb_pos_x"] > turb_pos_x
    assert data["turb_pos_y"] > turb_pos_y


def test_StructuredTemplateExtras_write_grid(mocker, structuredextras):
    
    mock_write_fm_rectangle = mocker.patch(
                    "snl_d3d_cec_verify.template.write_structured_rectangle",
                    autospec=True)
    
    case = CaseStudy()
    project_path = "mock_template"
    
    structuredextras.write_grid(project_path,
                                case.dx,
                                case.dy,
                                case.x0,
                                case.x1,
                                case.y0,
                                case.y1)
    
    mock_write_fm_rectangle.assert_called_with(project_path,
                                                case.dx,
                                                case.dy,
                                                case.x0,
                                                case.x1,
                                                case.y0,
                                                case.y1)


def test_package_template_path():
    template_type = "fm"
    expected = Path("snl_d3d_cec_verify") / "templates" / template_type
    result = _package_template_path(template_type)
    assert str(expected) in str(result)


def test_template_bad_type():
    
    with pytest.raises(ValueError) as excinfo:
        Template("mock")
    
    assert "type not recognised" in str(excinfo)


def test_template_call_too_many_cases():
    
    template = Template()
    case = CaseStudy(dx=[1, 2])
    
    with pytest.raises(ValueError) as excinfo:
        template(case, "mock")
    
    assert "case study must have length one" in str(excinfo)


def test_template_fm_call(mocker, tmp_path):
    
    mock_copy = mocker.patch("snl_d3d_cec_verify.template.copy_after",
                             autospec=True)
    mocker.patch("snl_d3d_cec_verify.template.write_fm_rectangle",
                 autospec=True)
    
    exist_ok = True
    case = CaseStudy()
    project_path = "mock_template"
    
    excluded_fields = ["dx", "dy"]
    expected_fields = [field for field in case.fields
                                           if field not in excluded_fields]
    
    template = Template(template_path=tmp_path, exist_ok=exist_ok)
    template(case, project_path)
    
    mock_copy.assert_called()
    mock_copy_kwargs = mock_copy.call_args.kwargs
    
    assert set(mock_copy.call_args.args) == set(
                                        [Path(template._template_tmp.name),
                                         Path(project_path)])
    assert set(expected_fields) <= set(mock_copy_kwargs["data"])
    assert mock_copy_kwargs["exist_ok"] is exist_ok
    assert mock_copy_kwargs["data"]["horizontal_momentum_filter"] == 1
    assert mock_copy_kwargs["data"]["stats_interval"] == ''


def test_template_structured_call(mocker, tmp_path):
    
    m0 = n0 = 1
    m1 = 20
    n1 = 6
    
    grid_return = {"m0": m0,
                   "m1": m1,
                   "n0": n0,
                   "n1": n1}
    
    mock_copy = mocker.patch("snl_d3d_cec_verify.template.copy_after",
                             autospec=True)
    mock_copy.return_value.__enter__.return_value = {}
    
    mocker.patch("snl_d3d_cec_verify.template.write_structured_rectangle",
                 return_value=grid_return,
                 autospec=True)
    
    exist_ok = True
    case = CaseStudy()
    project_path = "mock_template"
    
    excluded_fields = ["dx", "dy"]
    expected_fields = [field for field in case.fields
                                           if field not in excluded_fields]
    
    template = Template(template_type="structured",
                        template_path=tmp_path,
                        exist_ok=exist_ok)
    template(case, project_path)
    
    mock_copy.assert_called()
    mock_copy_kwargs = mock_copy.call_args.kwargs
    mock_copy_data = mock_copy.return_value.__enter__.return_value
    
    assert set(mock_copy.call_args.args) == set(
                                        [Path(template._template_tmp.name),
                                         Path(project_path)])
    assert set(expected_fields) <= set(mock_copy_kwargs["data"])
    assert mock_copy_kwargs["exist_ok"] is exist_ok
    
    for key, value in grid_return.items():
        assert mock_copy_data[key] == value
