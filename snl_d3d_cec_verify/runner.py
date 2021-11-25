# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import subprocess
from typing import Optional, TYPE_CHECKING, Union
from pathlib import Path

from .cases import CaseStudy, Template
from .copier import copy
from .gridfm import write_gridfm_rectangle
from .types import StrOrPath



class Runner:
    
    def __init__(self, template_path: StrOrPath,
                       d3d_bin_path: StrOrPath):
        self._template_path = template_path
        self._d3d_bin_path = d3d_bin_path
        self.cases = CaseStudy.null()
        return
    
    def make_case_files(self, case: CaseStudy,
                              project_path: StrOrPath,
                              exist_ok: bool = False):
        
        if len(case) != 1:
            raise ValueError("Case study must have length one")
        
        # Copy templated files
        data = {field: value.value
                    for field, value in zip(case.fields, case.values)
                                            if isinstance(value, Template)}
        
        copy(self._template_path, project_path, data=data, exist_ok=exist_ok)
        write_gridfm_rectangle(Path(project_path) / "input" / "FlowFM_net.nc",
                               case.dx,
                               case.dy)
    
    def __call__(self, case: CaseStudy
                       project_path: Optional[StrOrPath] = None):
        pass
        

def run_dflowfm(d3d_bin_path: StrOrPath,
                project_path: StrOrPath,
                omp_num_threads: int = 1,
                show_stdout: bool = False):
    
    rundir = Path(project_path) / "input"
    run_dflowfm_path = Path(d3d_bin_path).joinpath("x64",
                                                   "dflowfm",
                                                   "scripts",
                                                   "run_dflowfm.bat")
    
    env = dict(os.environ)
    env['OMP_NUM_THREADS'] = f"{omp_num_threads}"
    sp = subprocess.Popen([run_dflowfm_path, "FlowFM.mdu"],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          cwd=rundir,
                          env=env)
    out, err = sp.communicate()
    
    if out and show_stdout:
        print('stdout      :', out.decode('utf-8'))
    
    if err:
        print('stderr      :', err.decode('utf-8'))
        raise RuntimeError("Delft3D simulation failure")
