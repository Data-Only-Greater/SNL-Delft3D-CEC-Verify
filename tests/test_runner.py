# -*- coding: utf-8 -*-

import platform
from pathlib import Path
from subprocess import Popen

import pytest

from snl_d3d_cec_verify.runner import (_get_dflowfm_entry_point,
                                       run_dflowfm,
                                       Runner,
                                       LiveRunner)


def test_get_dflowfm_entry_point(data_dir):
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    if os_name == 'Windows':
        expected_entry_point = Path(d3d_bin_path).joinpath("x64",
                                                           "dflowfm",
                                                           "scripts",
                                                           "run_dflowfm.bat")
    else:
        expected_entry_point = Path(d3d_bin_path) / "run_dflowfm.sh"
    
    assert _get_dflowfm_entry_point(d3d_bin_path) == expected_entry_point


def test_get_dflowfm_entry_point_unsupported_os(mocker):
    
    os_name = "DOS"
    mocker.patch('snl_d3d_cec_verify.runner.platform.system',
                 return_value=os_name)
    
    with pytest.raises(OSError) as excinfo:
        _get_dflowfm_entry_point("mock")
    
    assert f"'{os_name}' not supported" in str(excinfo)


def test_get_dflowfm_entry_point_missing_script(tmp_path):
    
    d3d_bin_path = "mock_bin"
    
    with pytest.raises(FileNotFoundError) as excinfo:
        _get_dflowfm_entry_point(d3d_bin_path)
    
    assert "script could not be found" in str(excinfo)
    assert d3d_bin_path in str(excinfo)


def test_run_dflowfm( mocker, tmp_path, data_dir):
    
    from snl_d3d_cec_verify.runner import subprocess
    
    spy_popen = mocker.spy(subprocess, 'Popen')
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    omp_num_threads = 99
    
    sp = run_dflowfm(d3d_bin_path,
                     tmp_path,
                     omp_num_threads)
    
    assert isinstance(sp, Popen)
    
    cwd = spy_popen.call_args.kwargs['cwd']
    env = spy_popen.call_args.kwargs['env']
    
    assert cwd == tmp_path
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads


def test_run_dflowfm_missing_input_folder(mocker):
    
    mocker.patch("snl_d3d_cec_verify.runner._get_dflowfm_entry_point")
    d3d_bin_path = "mock_bin"
    project_path = "mock_project"
    
    with pytest.raises(FileNotFoundError) as excinfo:
        for _ in run_dflowfm(d3d_bin_path,
                             project_path):
            pass
    
    assert "Model folder could not be found" in str(excinfo)
    assert project_path in str(excinfo)


def test_runner_call(capsys, tmp_path, data_dir):
    
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    runner = Runner(d3d_bin_path, show_stdout=True)
    runner(tmp_path)
    captured = capsys.readouterr()
    
    assert "stdout" in captured.out


def test_runner_call_relative_input_parts_none(capsys, tmp_path, data_dir):
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    runner = Runner(d3d_bin_path, show_stdout=True, relative_input_parts=None)
    runner(tmp_path)
    captured = capsys.readouterr()
    
    assert "stdout" in captured.out


def test_runner_call_error(capsys, tmp_path, mocker, data_dir):
    
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
        script = "run.bat"
    else:
        d3d_bin_path = data_dir / "linux"
        script = "run.bat"
    
    run_path = Path(data_dir) / "error" / script
    
    mocker.patch('snl_d3d_cec_verify.runner._get_dflowfm_entry_point',
                  return_value=run_path)
    
    runner = Runner(d3d_bin_path, show_stdout=True)
    
    with pytest.raises(RuntimeError) as excinfo:
        runner(tmp_path)
    
    captured = capsys.readouterr()
    
    assert "simulation failure" in str(excinfo)
    assert "stderr" in captured.out
    assert "Error first line" in captured.out
    assert "Error third line" in captured.out


def test_liverunner_call(tmp_path, data_dir):
    
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    runner = LiveRunner(d3d_bin_path)
    out = ""
    
    for line in runner(tmp_path):
        out += line
    
    assert "OMP_NUM_THREADS is already defined" in out


def test_liverunner_call_relative_input_parts_none(tmp_path, data_dir):
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    runner = LiveRunner(d3d_bin_path, relative_input_parts=None)
    out = ""
    
    for line in runner(tmp_path):
        out += line
    
    assert "OMP_NUM_THREADS is already defined" in out


def test_liverunner_call_error(tmp_path, mocker, data_dir):
    
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
        script = "run.bat"
    else:
        d3d_bin_path = data_dir / "linux"
        script = "run.bat"
    
    run_path = Path(data_dir) / "error" / script
    
    mocker.patch('snl_d3d_cec_verify.runner._get_dflowfm_entry_point',
                  return_value=run_path)
    
    runner = LiveRunner(d3d_bin_path)
    out = ""
    
    with pytest.raises(RuntimeError) as excinfo:
        for line in runner(tmp_path):
            out += line
    
    assert "simulation failure" in str(excinfo)
    assert "Error first line" in out
    assert "Error third line" in out
