# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import platform
import subprocess
from typing import Optional
from pathlib import Path
from dataclasses import dataclass

from .types import StrOrPath


@dataclass
class Runner:
    d3d_bin_path: StrOrPath
    omp_num_threads: int = 1
    show_stdout: bool = False
    
    def __call__(self, project_path: StrOrPath,
                       omp_num_threads: Optional[int] = None,
                       show_stdout: Optional[bool] = None):
        
        if omp_num_threads is None:
            omp_num_threads = self.omp_num_threads
        
        if show_stdout is None:
            show_stdout = self.show_stdout
        
        run_dflowfm(self.d3d_bin_path,
                    project_path,
                    omp_num_threads,
                    show_stdout)


def run_dflowfm(d3d_bin_path: StrOrPath,
                project_path: StrOrPath,
                omp_num_threads: int = 1,
                show_stdout: bool = False):
    
    rundir = Path(project_path) / "input"
    os_name = platform.system()
    
    # TODO: convert to match-case when 3.10 is supported by deps
    if os_name == 'Windows':
        run_dflowfm_path = Path(d3d_bin_path).joinpath("x64",
                                                       "dflowfm",
                                                       "scripts",
                                                       "run_dflowfm.bat")
    elif os_name == 'Linux':
        run_dflowfm_path = Path(d3d_bin_path) / "run_dflowfm.sh"
    else:
        raise OSError(f"Operating system '{os_name}' not supported")
    
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
