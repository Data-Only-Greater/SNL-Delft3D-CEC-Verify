# -*- coding: utf-8 -*-

import pytest

from snl_d3d_cec_verify._paths import find_path


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
