# -*- coding: utf-8 -*-

import platform
from pathlib import Path

import pytest

from snl_d3d_cec_verify.runner import run_dflowfm, Runner


def test_run_dflowfm(capsys, mocker, tmp_path, data_dir):
    
    from snl_d3d_cec_verify.runner import subprocess
    
    spy_popen = mocker.spy(subprocess, 'Popen')
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    omp_num_threads = 99
    
    run_dflowfm(d3d_bin_path,
                tmp_path,
                omp_num_threads,
                show_stdout=True)
    
    dflowfm_path = spy_popen.call_args.args[0][0]
    cwd = spy_popen.call_args.kwargs['cwd']
    env = spy_popen.call_args.kwargs['env']
    captured = capsys.readouterr()
    
    if os_name == 'Windows':
        expected_dflowfm_path = Path(d3d_bin_path).joinpath("x64",
                                                            "dflowfm",
                                                            "scripts",
                                                            "run_dflowfm.bat")
    else:
        expected_dflowfm_path = Path(d3d_bin_path) / "run_dflowfm.sh"
    
    assert dflowfm_path == expected_dflowfm_path
    assert cwd == tmp_path
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads
    assert 'stdout' in captured.out
    assert 'dflowfm' in captured.out


def test_run_dflowfm_error(capsys, mocker, tmp_path, data_dir):
    
    process_mock = mocker.Mock()
    attrs = {'communicate.return_value': (''.encode(), 
                                          'error'.encode())}
    process_mock.configure_mock(**attrs)
    
    mock_popen = mocker.patch('snl_d3d_cec_verify.runner.subprocess.Popen',
                              return_value=process_mock)
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    omp_num_threads = 99
    
    with pytest.raises(RuntimeError) as excinfo:
        run_dflowfm(d3d_bin_path,
                    tmp_path,
                    omp_num_threads,
                    show_stdout=True)
    
    dflowfm_path = mock_popen.call_args.args[0][0]
    cwd = mock_popen.call_args.kwargs['cwd']
    env = mock_popen.call_args.kwargs['env']
    captured = capsys.readouterr()
    os_name = platform.system()
    
    if os_name == 'Windows':
        expected_dflowfm_path = Path(d3d_bin_path).joinpath("x64",
                                                            "dflowfm",
                                                            "scripts",
                                                            "run_dflowfm.bat")
    else:
        expected_dflowfm_path = Path(d3d_bin_path) / "run_dflowfm.sh"
    
    assert dflowfm_path == expected_dflowfm_path
    assert cwd == tmp_path
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads
    assert 'stderr' in captured.out
    assert 'error' in captured.out
    assert "simulation failure" in str(excinfo)


def test_run_dflowfm_unsupported_os(mocker):
    
    os_name = "DOS"
    mocker.patch('snl_d3d_cec_verify.runner.platform.system',
                 return_value=os_name)
    
    d3d_bin_path = "mock_bin"
    project_path = "mock_project"
    
    with pytest.raises(OSError) as excinfo:
        run_dflowfm(d3d_bin_path,
                    project_path)
    
    assert f"'{os_name}' not supported" in str(excinfo)


def test_run_dflowfm_missing_script(tmp_path):
    
    d3d_bin_path = "mock_bin"
    
    with pytest.raises(FileNotFoundError) as excinfo:
        run_dflowfm(d3d_bin_path,
                    tmp_path)
    
    assert "script could not be found" in str(excinfo)
    assert d3d_bin_path in str(excinfo)


def test_run_dflowfm_missing_input_folder(tmp_path, data_dir):
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    project_path = "mock_project"
    
    with pytest.raises(FileNotFoundError) as excinfo:
        run_dflowfm(d3d_bin_path,
                    project_path)
    
    assert "Model folder could not be found" in str(excinfo)
    assert project_path in str(excinfo)


def test_runner_call(mocker):
    
    mock = mocker.patch('snl_d3d_cec_verify.runner.run_dflowfm')
    
    d3d_bin_path = "mock_bin"
    project_path = "mock_project"
    runner = Runner(d3d_bin_path)
    runner(project_path)
    
    mock.assert_called_with(d3d_bin_path,
                            Path(project_path) / "input",
                            runner.omp_num_threads,
                            runner.show_stdout)
