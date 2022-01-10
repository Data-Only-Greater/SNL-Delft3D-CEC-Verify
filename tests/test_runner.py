# -*- coding: utf-8 -*-

import platform
from pathlib import Path

import pytest

from snl_d3d_cec_verify.runner import (_get_dflowfm_entry_point,
                                       run_dflowfm,
                                       Runner)


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
    
    runner = run_dflowfm(d3d_bin_path,
                         tmp_path,
                         omp_num_threads)
    
    output = ""
    
    for msg in runner:
        output += msg
    
    with pytest.raises(StopIteration):
        next(runner)
    
    cwd = spy_popen.call_args.kwargs['cwd']
    env = spy_popen.call_args.kwargs['env']
    
    assert cwd == tmp_path
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads
    assert 'dflowfm' in output


def test_run_dflowfm_error(capsys, mocker, tmp_path, data_dir):
    
    process_mock = mocker.Mock()
    stdout_mock = mocker.Mock()
    stdout_mock.readline.side_effect = ['normal'.encode(),
                                        ''.encode()]
    stdout_mock.__enter__ = mocker.Mock(return_value='foo')
    stdout_mock.__exit__ = mocker.Mock(return_value='bar')
    stderr_mock = mocker.Mock()
    stderr_mock.readline.side_effect = ['error'.encode(),
                                        ''.encode()]
    stderr_mock.__enter__  = mocker.Mock(return_value='foo')
    stderr_mock.__exit__ = mocker.Mock(return_value='bar')
    
    process_mock.stdout = stdout_mock
    process_mock.stderr = stderr_mock
    
    mock_popen = mocker.patch('snl_d3d_cec_verify.runner.subprocess.Popen',
                              return_value=process_mock)
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    omp_num_threads = 99
    
    with pytest.raises(RuntimeError) as excinfo:
        for _ in run_dflowfm(d3d_bin_path,
                             tmp_path,
                             omp_num_threads):
            pass
    
    cwd = mock_popen.call_args.kwargs['cwd']
    env = mock_popen.call_args.kwargs['env']
    captured = capsys.readouterr()
    os_name = platform.system()
    
    assert cwd == tmp_path
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads
    assert 'error' in captured.out
    assert "simulation failure" in str(excinfo)


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


def test_runner_call(mocker):
    
    mock = mocker.patch('snl_d3d_cec_verify.runner.run_dflowfm')
    
    d3d_bin_path = "mock_bin"
    project_path = "mock_project"
    runner = Runner(d3d_bin_path)
    
    for _ in runner(project_path):
        pass
    
    mock.assert_called_with(d3d_bin_path,
                            Path(project_path) / "input",
                            runner.omp_num_threads)


def test_runner_call_relative_input_parts_none(mocker):
    
    mock = mocker.patch('snl_d3d_cec_verify.runner.run_dflowfm')
    
    d3d_bin_path = "mock_bin"
    project_path = "mock_project"
    runner = Runner(d3d_bin_path, relative_input_parts=None)
    runner(project_path)
    
    for _ in runner(project_path):
        pass
    
    mock.assert_called_with(d3d_bin_path,
                            Path(project_path),
                            runner.omp_num_threads)
