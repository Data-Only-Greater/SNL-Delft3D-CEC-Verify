# -*- coding: utf-8 -*-

from pathlib import Path

import pytest

from snl_d3d_cec_verify.runner import run_dflowfm, Runner


def test_run_dflowfm(capsys, mocker):
    
    process_mock = mocker.Mock()
    attrs = {'communicate.return_value': ('output'.encode(), 
                                          ''.encode())}
    process_mock.configure_mock(**attrs)
    
    mock_popen = mocker.patch('snl_d3d_cec_verify.runner.subprocess.Popen',
                              return_value=process_mock)
    
    d3d_bin_path = "mock_bin"
    project_path = "mock_project"
    omp_num_threads = 99
    
    run_dflowfm(d3d_bin_path,
                project_path,
                omp_num_threads,
                show_stdout=True)
    
    
    dflowfm_path = mock_popen.call_args.args[0][0]
    cwd = mock_popen.call_args.kwargs['cwd']
    env = mock_popen.call_args.kwargs['env']
    captured = capsys.readouterr()

    
    assert dflowfm_path == Path(d3d_bin_path).joinpath("x64",
                                                       "dflowfm",
                                                       "scripts",
                                                       "run_dflowfm.bat")
    assert cwd == Path(project_path) / "input"
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads
    assert 'stdout' in captured.out
    assert 'output' in captured.out


def test_run_dflowfm_error(capsys, mocker):
    
    process_mock = mocker.Mock()
    attrs = {'communicate.return_value': (''.encode(), 
                                          'error'.encode())}
    process_mock.configure_mock(**attrs)
    
    mock_popen = mocker.patch('snl_d3d_cec_verify.runner.subprocess.Popen',
                              return_value=process_mock)
    
    d3d_bin_path = "mock_bin"
    project_path = "mock_project"
    omp_num_threads = 99
    
    with pytest.raises(RuntimeError) as excinfo:
        run_dflowfm(d3d_bin_path,
                    project_path,
                    omp_num_threads,
                    show_stdout=True)
    
    dflowfm_path = mock_popen.call_args.args[0][0]
    cwd = mock_popen.call_args.kwargs['cwd']
    env = mock_popen.call_args.kwargs['env']
    captured = capsys.readouterr()
    
    assert dflowfm_path == Path(d3d_bin_path).joinpath("x64",
                                                       "dflowfm",
                                                       "scripts",
                                                       "run_dflowfm.bat")
    assert cwd == Path(project_path) / "input"
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads
    assert 'stderr' in captured.out
    assert 'error' in captured.out
    assert "simulation failure" in str(excinfo)


def test_runner_call(mocker):
    
    mock = mocker.patch('snl_d3d_cec_verify.runner.run_dflowfm')
    
    d3d_bin_path = "mock_bin"
    project_path = "mock_project"
    runner = Runner(d3d_bin_path)
    runner(project_path)
    
    mock.assert_called_with(d3d_bin_path,
                            project_path,
                            runner.omp_num_threads,
                            runner.show_stdout)
