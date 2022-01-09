# -*- coding: utf-8 -*-

import os
from filecmp import cmp

import pytest
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from snl_d3d_cec_verify.copier import (_get_posix_relative_paths,
                                       _template_copy,
                                       _basic_copy,
                                       copy)


def test_get_posix_relative_paths(tmp_path):
    
    # Fake some files
    content = "content"
    
    p = tmp_path / "hello.txt"
    p.write_text(content)
    
    d = tmp_path / "sub"
    d.mkdir()
    
    p = d / "subhello.txt"
    p.write_text(content)
    
    # Run the test
    test = _get_posix_relative_paths(tmp_path)
    assert test == ['hello.txt', 'sub', 'sub/subhello.txt']


def test_template_copy(tmp_path):
    
    # Fake a src and destination
    src_path = tmp_path / "src_path"
    src_path.mkdir()
    
    sub_d = src_path / "sub"
    sub_d.mkdir()
    
    p = sub_d / "hello.txt"
    p.write_text("{{ x }}\n")
    
    dst_path = tmp_path / "dst_path"
    dst_path.mkdir()
    
    sub_d = dst_path / "sub"
    sub_d.mkdir()
    
    # Create a jinja environment
    env = Environment(loader=FileSystemLoader(str(src_path)),
                      keep_trailing_newline=True)
    
    # Set the content value
    expected_text = "content"
    data = {"x": expected_text}
    
    # Run the test
    _template_copy(env, dst_path, "sub/hello.txt", data)
    expected_p = dst_path / "sub" / "hello.txt"
    
    assert expected_p.exists()
    
    text = expected_p.read_text()
    assert text == expected_text + "\n"


@pytest.mark.parametrize("value,         expected", [
                         (1e-6,          "1E-06          "),
                         (1,             "1              "),
                         (1 + 1e-8,      "1.00000001     "),
                         (1.00000001e-6, "1.00000001E-06 ")])
def test_template_copy_numeric(tmp_path, value, expected):
    
    # Fake a src and destination
    src_path = tmp_path / "src_path"
    src_path.mkdir()
    
    sub_d = src_path / "sub"
    sub_d.mkdir()
    
    p = sub_d / "numbers.txt"
    p.write_text("{{ '{:<15.9G}'.format(x) }}")
    
    dst_path = tmp_path / "dst_path"
    dst_path.mkdir()
    
    sub_d = dst_path / "sub"
    sub_d.mkdir()
    
    # Create a jinja environment
    env = Environment(loader=FileSystemLoader(str(src_path)),
                      keep_trailing_newline=True)
    
    # Set the content value
    data = {"x": value}
    
    # Run the test
    _template_copy(env, dst_path, "sub/numbers.txt", data)
    expected_p = dst_path / "sub" / "numbers.txt"
    
    assert expected_p.exists()
    
    text = expected_p.read_text()
    assert text == expected


def test_template_copy_unicode_decode_error(tmp_path):
    
    # Fake a src and destination
    dst_path = tmp_path / "dst_path"
    dst_path.mkdir()
    
    src_path = tmp_path / "src_path"
    src_path.mkdir()
    
    p = src_path / "hello.bin"
    p.write_bytes(os.urandom(1024))
    
    # Create a jinja environment
    env = Environment(loader=FileSystemLoader(str(src_path)),
                      keep_trailing_newline=True)
    
    # Run the test
    with pytest.raises(UnicodeDecodeError) as excinfo:
        _template_copy(env, dst_path, "hello.bin", {})
    
    assert ("invalid start byte" in str(excinfo) or
            "invalid continuation byte" in str(excinfo))


def test_template_copy_template_not_found(tmp_path):
    
    # Fake a src and destination
    dst_path = tmp_path / "dst_path"
    dst_path.mkdir()
    
    src_path = tmp_path / "src_path"
    src_path.mkdir()
    
    sub_d = src_path / "sub"
    sub_d.mkdir()
    
    # Create a jinja environment
    env = Environment(loader=FileSystemLoader(str(src_path)),
                      keep_trailing_newline=True)
    
    # Run the test
    with pytest.raises(TemplateNotFound) as excinfo:
        _template_copy(env, dst_path, "sub", {})
    
    assert "sub" in str(excinfo)


def test_basic_copy_dir(tmp_path):
    
    # Fake a src and destination
    src_path = tmp_path / "src_path"
    src_path.mkdir()
    
    sub_d = src_path / "sub" / "sub"
    sub_d.mkdir(parents=True)
    
    dst_path = tmp_path / "dst_path"
    dst_path.mkdir()
    
    sub_d = dst_path / "sub"
    sub_d.mkdir()
    
    # Run the test
    _basic_copy(src_path, dst_path, "sub/sub")
    expected_d = dst_path / "sub" / "sub"
    
    assert expected_d.exists()
    assert expected_d.is_dir()


def test_basic_copy_file(tmp_path):
    
    # Fake a src and destination
    src_path = tmp_path / "src_path"
    src_path.mkdir()
    
    sub_d = src_path / "sub"
    sub_d.mkdir()
    
    p = sub_d / "hello.bin"
    p.write_bytes(os.urandom(1024))
    
    dst_path = tmp_path / "dst_path"
    dst_path.mkdir()
    
    sub_d = dst_path / "sub"
    sub_d.mkdir()
    
    # Run the test
    _basic_copy(src_path, dst_path, "sub/hello.bin")
    expected_p = dst_path / "sub" / "hello.bin"
    
    assert expected_p.exists()
    assert cmp(p, expected_p)


@pytest.fixture
def test_path(tmp_path):
    
    # Fake a src and destination
    src_path = tmp_path / "src_path"
    src_path.mkdir()
    
    p = src_path / "hello.txt"
    p.write_text("content")
    
    p = src_path / "hello.bin"
    p.write_bytes(os.urandom(1024))
    
    dst_path = tmp_path / "dst_path"
    
    return (src_path, dst_path)


def test_copy_src_path_missing(tmp_path):
    
    src_path = tmp_path / "src_path"
    dst_path = tmp_path / "dst_path"
    
    with pytest.raises(ValueError) as excinfo:
        copy(src_path, dst_path)
    
    assert "src_path does not exist" in str(excinfo)


def test_copy_dst_path_missing(test_path):
    
    src_path, dst_path = test_path
    copy(src_path, dst_path)
    expected_txt = dst_path / "hello.txt"
    expected_bin = dst_path / "hello.bin"
    
    assert expected_txt.exists()
    assert expected_bin.exists()
    
    text = expected_txt.read_text()
    assert text == "content"


def test_copy_dst_path_empty(test_path):
    
    src_path, dst_path = test_path
    dst_path.mkdir()
    
    copy(src_path, dst_path)
    expected_txt = dst_path / "hello.txt"
    expected_bin = dst_path / "hello.bin"
    
    assert expected_txt.exists()
    assert expected_bin.exists()
    
    text = expected_txt.read_text()
    assert text == "content"


def test_copy_dst_path_contains_error(test_path):
    
    src_path, dst_path = test_path
    dst_path.mkdir()
    
    p = dst_path / "anything.txt"
    p.write_text("content")
    
    with pytest.raises(FileExistsError) as excinfo:
        copy(src_path, dst_path)
    
    assert "contains files" in str(excinfo)


def test_copy_dst_path_contains_exist_ok(test_path):
    
    src_path, dst_path = test_path
    dst_path.mkdir()
    
    p = dst_path / "anything.txt"
    p.write_text("content")
    
    sub_d = dst_path / "sub"
    sub_d.mkdir()
    
    copy(src_path, dst_path, exist_ok=True)
    expected_txt = dst_path / "hello.txt"
    expected_bin = dst_path / "hello.bin"
    
    assert expected_txt.exists()
    assert expected_bin.exists()
    
    text = expected_txt.read_text()
    assert text == "content"


def test_copy_dst_path_contains_unknown_file(test_path, mocker):
    
    src_path, dst_path = test_path
    dst_path.mkdir()
    
    p = dst_path / "anything.txt"
    p.write_text("content")
    
    # Mock discovery of unhandled file type
    mock_p = mocker.MagicMock()
    mock_p.is_file = mocker.MagicMock(return_value=False)
    mock_p.is_dir = mocker.MagicMock(return_value=False)
    
    to_copy = mocker.MagicMock()
    to_copy.exists = mocker.MagicMock(return_value=True)
    to_copy.iterdir = mocker.MagicMock(return_value=[mock_p])
    
    mocker.patch("snl_d3d_cec_verify.copier.Path",
                 return_value=to_copy)
    
    with pytest.raises(RuntimeError) as excinfo:
        copy(src_path, dst_path, exist_ok=True)
    
    assert "unhandled file type" in str(excinfo)
