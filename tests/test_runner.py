# -*- coding: utf-8 -*-

import platform
from pathlib import Path
from subprocess import Popen

import pytest

from snl_d3d_cec_verify.runner import (_get_entry_point,
                                       _run_script,
                                       run_dflowfm,
                                       run_dflow2d3d,
                                       _find_path,
                                       _BaseModelRunner,
                                       _FMModelRunner,
                                       _StructuredModelRunner,
                                       _run_model,
                                       Runner,
                                       LiveRunner)


def test_get_entry_point(data_dir):
    
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
    
    assert _get_entry_point(d3d_bin_path,
                            "dflowfm") == expected_entry_point


def test_get_entry_point_unsupported_os(mocker):
    
    os_name = "DOS"
    mocker.patch('snl_d3d_cec_verify.runner.platform.system',
                 return_value=os_name,
                 autospec=True)
    
    with pytest.raises(OSError) as excinfo:
        _get_entry_point("mock", "mock")
    
    assert f"'{os_name}' not supported" in str(excinfo)


def test_get_entry_point_missing_script(tmp_path):
    
    d3d_bin_path = "mock_bin"
    name = "mock_name"
    
    with pytest.raises(FileNotFoundError) as excinfo:
        _get_entry_point(d3d_bin_path, name)
    
    assert "script could not be found" in str(excinfo)
    assert d3d_bin_path in str(excinfo)
    assert name in str(excinfo)


def test_run_script_missing_input_folder(mocker):
    
    mocker.patch("snl_d3d_cec_verify.runner._get_entry_point",
                 autospec=True)
    d3d_bin_path = "mock_bin"
    model_path = "mock_project"
    
    with pytest.raises(FileNotFoundError) as excinfo:
        _run_script("mock", d3d_bin_path, model_path)
    
    assert "Model folder could not be found" in str(excinfo)
    assert model_path in str(excinfo)


def test_run_script(mocker, tmp_path, data_dir):
    
    from snl_d3d_cec_verify.runner import subprocess
    
    expected_entry = "mock_entry"
    expected_args = ["mock1", "mock2"]
    
    mock_popen = mocker.patch.object(subprocess,
                                     'Popen',
                                     autospec=True)
    mocker.patch('snl_d3d_cec_verify.runner._get_entry_point',
                 return_value=Path(expected_entry),
                 autospec=True)
    
    omp_num_threads = 99
    
    sp = _run_script("mock",
                     "mock",
                     tmp_path,
                     omp_num_threads,
                     *expected_args)
    
    assert isinstance(sp, Popen)
    
    popen_args = mock_popen.call_args.args[0]
    cwd = mock_popen.call_args.kwargs['cwd']
    env = mock_popen.call_args.kwargs['env']
    
    assert Path(popen_args[0]).name == expected_entry
    assert popen_args[1:] == expected_args
    assert cwd == tmp_path
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads


def test_run_dflowfm(mocker, tmp_path, data_dir):
    
    from snl_d3d_cec_verify.runner import subprocess
    
    model_file = "mock.mdu"
    
    spy_popen = mocker.spy(subprocess, 'Popen')
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    omp_num_threads = 99
    
    sp = run_dflowfm(d3d_bin_path,
                     tmp_path,
                     model_file,
                     omp_num_threads)
    
    assert isinstance(sp, Popen)
    
    popen_args = spy_popen.call_args.args[0]
    cwd = spy_popen.call_args.kwargs['cwd']
    env = spy_popen.call_args.kwargs['env']
    
    assert "dflowfm" in popen_args[0]
    assert popen_args[1:] == [model_file]
    assert cwd == tmp_path
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads


def test_run_dflow2d3d(mocker, tmp_path, data_dir):
    
    from snl_d3d_cec_verify.runner import subprocess
    
    spy_popen = mocker.spy(subprocess, 'Popen')
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    omp_num_threads = 99
    
    sp = run_dflow2d3d(d3d_bin_path,
                       tmp_path,
                       omp_num_threads)
    
    assert isinstance(sp, Popen)
    
    popen_args = spy_popen.call_args.args[0]
    cwd = spy_popen.call_args.kwargs['cwd']
    env = spy_popen.call_args.kwargs['env']
    
    assert "dflow2d3d" in popen_args[0]
    assert cwd == tmp_path
    assert int(env['OMP_NUM_THREADS']) == omp_num_threads


def test_find_path_multiple_files(tmp_path):
    
    ext = ".mdu"
    p = tmp_path / f"mock1{ext}"
    p.write_text('Mock')
    p = tmp_path / f"mock2{ext}"
    p.write_text('Mock')
    
    with pytest.raises(FileNotFoundError) as excinfo:
        _find_path(tmp_path, ext)
    
    assert f"Multiple files detected with signature '*{ext}'" in str(excinfo)


def test_find_path_multiple_named_files(tmp_path):
    
    file_root = "mock"
    ext = ".mdu"
    p = tmp_path / f"{file_root}{ext}"
    p.write_text('Mock')
    
    sub_dir = tmp_path / "input"
    sub_dir.mkdir()
    p = sub_dir / f"{file_root}{ext}"
    p.write_text('Mock')
    
    with pytest.raises(FileNotFoundError) as excinfo:
        _find_path(tmp_path, ext, file_root)
    
    assert f"signature '{file_root}{ext}'" in str(excinfo)


@pytest.mark.parametrize("file_name, root, valid", [
                                ("mock.mdu", None, True),
                                ("", None, False),
                                ("mock.mdf", None, False),
                                ("mock.mdu", "mock", True),
                                ("mock.mdu", "not_mock", False)])
def test_find_path(tmp_path, file_name, root, valid):
    
    ext = ".mdu"
    
    if file_name:
        p = tmp_path / file_name
        p.write_text('Mock')
    
    if valid:
        expected = p
    else:
        expected = None
    
    test = _find_path(tmp_path, ext, root)
    
    assert test == expected


class MockModelRunner(_BaseModelRunner):
    
    def _get_model_path(self):
        return self.project_path
    
    def run_model(self):
        pass


@pytest.mark.parametrize("project_path, expected", [
                            (None, False),
                            (0, True)])
def test_BaseModelRunner_is_model(project_path, expected):
    test = MockModelRunner(project_path)
    assert test.is_model() is expected


def test_FMModelRunner_get_model_path(mocker):
    
    mock_find_path = mocker.patch('snl_d3d_cec_verify.runner._find_path',
                                  autospec=True)
    
    project_path = "mock"
    test = _FMModelRunner(project_path)
    test._get_model_path()
    
    mock_find_path.assert_called_once_with(project_path, ".mdu")


def test_FMModelRunner_run_model_path_missing_mdu(tmp_path):
    
    test = _FMModelRunner(tmp_path)
    
    with pytest.raises(FileNotFoundError) as excinfo:
        test.run_model("mock", "mock")
    
    assert "No .mdu file detected" in str(excinfo)


def test_FMModelRunner_run_model(mocker, tmp_path):
    
    mock_run_dflowfm = mocker.patch('snl_d3d_cec_verify.runner.run_dflowfm',
                                    autospec=True)
    
    file_name = "mock.mdu"
    p = tmp_path / file_name
    p.write_text('Mock')
    
    d3d_bin_path = "mock"
    omp_num_threads = 99
    
    test = _FMModelRunner(tmp_path)
    test.run_model(d3d_bin_path, omp_num_threads)
    
    mock_run_dflowfm.assert_called_once_with(d3d_bin_path,
                                             tmp_path,
                                             file_name,
                                             omp_num_threads)


def test_StructuredModelRunner_get_model_path(mocker):
    
    mock_find_path = mocker.patch('snl_d3d_cec_verify.runner._find_path',
                                  autospec=True)
    
    project_path = "mock"
    test = _StructuredModelRunner(project_path)
    test._get_model_path()
    
    mock_find_path.assert_called_once_with(project_path,
                                          '.xml',
                                          'config_d_hydro')


def test_StructuredModelRunner_run_model_path_missing_mdu(tmp_path):
    
    test = _StructuredModelRunner(tmp_path)
    
    with pytest.raises(FileNotFoundError) as excinfo:
        test.run_model("mock", "mock")
    
    assert 'No config_d_hydro.xml file detected' in str(excinfo)


def test_StructuredModelRunner_run_model(mocker, tmp_path):
    
    mock_run_dflow2d3d = mocker.patch(
                                'snl_d3d_cec_verify.runner.run_dflow2d3d',
                                autospec=True)
    
    file_name = "config_d_hydro.xml"
    p = tmp_path / file_name
    p.write_text('Mock')
    
    d3d_bin_path = "mock"
    omp_num_threads = 99
    
    test = _StructuredModelRunner(tmp_path)
    test.run_model(d3d_bin_path, omp_num_threads)
    
    mock_run_dflow2d3d.assert_called_once_with(d3d_bin_path,
                                               tmp_path,
                                               omp_num_threads)


def test_run_model_no_valid_files(tmp_path):
    
    with pytest.raises(FileNotFoundError) as excinfo:
        _run_model(tmp_path, "mock", "mock")
    
    assert "No valid model files detected" in str(excinfo)


@pytest.mark.parametrize("extras_name, file_name", [
                    ("_FMModelRunner", "mock.mdu"),
                    ("_StructuredModelRunner", "config_d_hydro.xml")])
def test_run_model(mocker, tmp_path, extras_name, file_name):
    
    mock_fm_run = mocker.patch(
                    f'snl_d3d_cec_verify.runner.{extras_name}.run_model')
    
    p = tmp_path / file_name
    p.write_text('Mock')
    
    d3d_bin_path = "mock"
    omp_num_threads = 99
    
    _run_model(tmp_path,
               d3d_bin_path,
               omp_num_threads)
    
    mock_fm_run.assert_called_once_with(d3d_bin_path,
                                        omp_num_threads)


def test_runner_call(capsys, tmp_path, data_dir):
    
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    p = input_dir / "mock.mdu"
    p.write_text('Mock')
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    runner = Runner(d3d_bin_path, show_stdout=True)
    runner(tmp_path)
    captured = capsys.readouterr()
    
    assert "stdout" in captured.out


def test_runner_call_error(capsys, tmp_path, mocker, data_dir):
    
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    p = input_dir / "mock.mdu"
    p.write_text('Mock')
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
        script = "run.bat"
    else:
        d3d_bin_path = data_dir / "linux"
        script = "run.sh"
    
    run_path = Path(data_dir) / "error" / script
    
    mocker.patch('snl_d3d_cec_verify.runner._get_entry_point',
                 return_value=run_path,
                 autospec=True)
    
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
    p = input_dir / "config_d_hydro.xml"
    p.write_text('Mock')
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
    else:
        d3d_bin_path = data_dir / "linux"
    
    runner = LiveRunner(d3d_bin_path)
    out = ""
    
    for line in runner(tmp_path):
        out += line
    
    assert "Configfile:config_d_hydro.xml" in out


def test_liverunner_call_error(tmp_path, mocker, data_dir):
    
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    p = input_dir / "config_d_hydro.xml"
    p.write_text('Mock')
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        d3d_bin_path = data_dir / "win"
        script = "run.bat"
    else:
        d3d_bin_path = data_dir / "linux"
        script = "run.sh"
    
    run_path = Path(data_dir) / "error" / script
    
    mocker.patch('snl_d3d_cec_verify.runner._get_entry_point',
                 return_value=run_path,
                 autospec=True)
    
    runner = LiveRunner(d3d_bin_path)
    out = ""
    
    with pytest.raises(RuntimeError) as excinfo:
        for line in runner(tmp_path):
            out += line
    
    assert "simulation failure" in str(excinfo)
    assert "Error first line" in out
    assert "Error third line" in out
