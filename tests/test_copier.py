# -*- coding: utf-8 -*-

import os
from filecmp import cmp

import pytest
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from snl_d3d_cec_verify.copier import (get_posix_relative_paths,
                                       template_copy,
                                       basic_copy)


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
    test = get_posix_relative_paths(tmp_path)
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
    template_copy(env, dst_path, "sub/hello.txt", data)
    expected_p = dst_path / "sub" / "hello.txt"
    
    assert expected_p.exists()
    
    text = expected_p.read_text()
    assert text == expected_text + "\n"


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
        template_copy(env, dst_path, "hello.bin", {})
    
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
        template_copy(env, dst_path, "sub", {})
    
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
    basic_copy(src_path, dst_path, "sub/sub")
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
    basic_copy(src_path, dst_path, "sub/hello.bin")
    expected_p = dst_path / "sub" / "hello.bin"
    
    assert expected_p.exists()
    assert cmp(p, expected_p)
