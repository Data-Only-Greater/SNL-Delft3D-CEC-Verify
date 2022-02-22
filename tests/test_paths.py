# -*- coding: utf-8 -*-

import pytest

from snl_d3d_cec_verify._paths import (_BaseModelFinder,
                                       get_model,
                                       find_path)


class MockModelFinder(_BaseModelFinder):
    
    @property
    def path(self):
        return self.project_path
    
    def run_model(self):
        pass


class MockNegModelFinder(_BaseModelFinder):
    
    @property
    def path(self):
        if self.project_path is None:
            return 0
        return None
    
    def run_model(self):
        pass


@pytest.mark.parametrize("project_path, expected", [
                            (None, False),
                            (0, True)])
def test_BaseModelRunner_is_model(project_path, expected):
    test = MockModelFinder(project_path)
    assert test.is_model() is expected


def test_get_model():
    test = get_model(0, MockNegModelFinder, MockModelFinder)
    assert isinstance(test, MockModelFinder)


def test_get_model_none():
    test = get_model(0, MockNegModelFinder, MockNegModelFinder)
    assert test is None


def test_find_path_multiple_files(tmp_path):
    
    ext = ".mdu"
    p = tmp_path / f"mock1{ext}"
    p.write_text('Mock')
    p = tmp_path / f"mock2{ext}"
    p.write_text('Mock')
    
    with pytest.raises(FileNotFoundError) as excinfo:
        find_path(tmp_path, ext)
    
    assert f"Multiple files detected with signature '*{ext}'" in str(excinfo)


def test_find_path_multiple_named_files(tmp_path):
    
    partial = "mock"
    ext = ".mdu"
    p = tmp_path / f"{partial}{ext}"
    p.write_text('Mock')
    
    sub_dir = tmp_path / "input"
    sub_dir.mkdir()
    p = sub_dir / f"{partial}{ext}"
    p.write_text('Mock')
    
    with pytest.raises(FileNotFoundError) as excinfo:
        find_path(tmp_path, ext, partial)
    
    assert f"signature '*{partial}*{ext}'" in str(excinfo)


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
    
    test = find_path(tmp_path, ext, root)
    
    assert test == expected
