# -*- coding: utf-8 -*-

import os
import shutil
import posixpath
from typing import List, Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .types import AnyByStrDict, StrOrPath


def copy(src_path: StrOrPath,
         dst_path: StrOrPath,
         data: Optional[AnyByStrDict] = None,
         exist_ok: bool = False):
    
    # Check that the template path exists
    if not Path(src_path).exists():
        raise ValueError("src_path does not exist")
    
    # Make the destination path
    to_copy = Path(dst_path)
    
    if to_copy.exists():
        
        is_empty = not any(to_copy.iterdir())
        
        if not is_empty and not exist_ok:
            raise FileExistsError("dst_path path contains files")
        
        for p in to_copy.iterdir():
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p)
            else:
                raise RuntimeError("unhandled file type")
    
    else:
        
        to_copy.mkdir(parents=True)
    
    relative_paths = get_posix_relative_paths(src_path)
    env = Environment(loader=FileSystemLoader(str(src_path)),
                      keep_trailing_newline=True)
    if data is None: data = {}
    
    for rel_path in relative_paths:
        try:
            template_copy(env, dst_path, rel_path, data)
        except (UnicodeDecodeError, TemplateNotFound):
            basic_copy(src_path, dst_path, rel_path)


def get_posix_relative_paths(root: StrOrPath) -> List[str]:
    
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


def template_copy(env: Environment,
                  dst_path: StrOrPath,
                  rel_path: str,
                  data: AnyByStrDict):
    
    to_copy = Path(dst_path).joinpath(rel_path)
    template = env.get_template(rel_path)
    rendered = template.render(**data)
    
    with open(to_copy, 'w') as f:
        f.write(rendered)


def basic_copy(src_path: StrOrPath,
               dst_path: StrOrPath,
               rel_path: str):
    
    from_copy = Path(src_path).joinpath(rel_path)
    to_copy = Path(dst_path).joinpath(rel_path)
    
    if from_copy.is_dir():
        to_copy.mkdir()
        return
    
    shutil.copy(from_copy, to_copy)
