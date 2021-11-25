# -*- coding: utf-8 -*-

import os
import shutil
import posixpath
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


def copy(src_path: Union[str, Path],
         dst_path: Union[str, Path],
         data: Optional[Dict[str, Any]] = None,
         rename_root: Optional[Dict[str, Any]] = None,
         exist_ok: bool = False):
    
    if data is None: data = {}
    
    # Make the destination path
    to_copy = Path(dst_path)
    
    if to_copy.exists():
        if not exist_ok:
            raise FileExistsError("Destination path already exists")
        else:
            shutil.rmtree(to_copy)
    
    to_copy.mkdir(parents=True)
    
    # Check that the template path exists
    if not Path(src_path).exists():
        raise ValueError("src_path does not exist")
    
    env = Environment(loader=FileSystemLoader(str(src_path)),
                      keep_trailing_newline=True)
    
    relative_paths = get_posix_relative_paths(src_path)
    
    for rel_path in relative_paths:
        try:
            template_copy(env, dst_path, rel_path, data)
        except (UnicodeDecodeError, TemplateNotFound):
            basic_copy(src_path, dst_path, rel_path)


def basic_copy(src_path: Union[str, Path],
               dst_path: Union[str, Path],
               rel_path: str):
    
    from_copy = Path(src_path).joinpath(rel_path)
    to_copy = Path(dst_path).joinpath(rel_path)
    
    if from_copy.is_dir():
        to_copy.mkdir()
        return
    
    shutil.copy(from_copy, to_copy)


def template_copy(env: Environment,
                  dst_path: Union[str, Path],
                  rel_path: str,
                  data: Dict[str, Any]):
    
    template = env.get_template(rel_path)
    rendered = template.render(**data)
    
    to_copy = Path(dst_path).joinpath(rel_path)
    
    with open(to_copy, 'w') as f:
        f.write(rendered)


def get_posix_relative_paths(root: Union[str, Path]) -> List[str]:
    
    all_paths = []
    
    for abs_dir, _, files in os.walk(root):
        
        rel_dir = os.path.relpath(abs_dir, root)
        
        if rel_dir == ".":
            rel_dir = ""
        else:
            posix_dir = rel_dir.replace(os.sep, posixpath.sep)
            all_paths.append(posix_dir)
        
        for file_name in files:
            rel_file = os.path.join(rel_dir, file_name)
            posix_file = rel_file.replace(os.sep, posixpath.sep)
            all_paths.append(posix_file)
    
    return all_paths
