# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import platform
import subprocess
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass

from .types import StrOrPath
from ._docs import docstringtemplate

__all__ = ["run_dflowfm"]


@dataclass
class Runner:
    """
    :param d3d_bin_path: path to the ``bin`` folder generated when compiling
        Delft3D
    
    """
    
    d3d_bin_path: StrOrPath
    omp_num_threads: int = 1
    show_stdout: bool = False
    
    def __post_init__(self):
        _get_dflowfm_entry_point(self.d3d_bin_path)
    
    def __call__(self, project_path: StrOrPath,
                       relative_input_parts: Optional[List[str]] = None,
                       omp_num_threads: Optional[int] = None,
                       show_stdout: Optional[bool] = None):
        """Run a simulation, given a prepared model.
        
        :param project_path: path to Delft3D project folder 
        :param relative_input_parts: list of components representing the
            relative path to folder containing the delft3D model files, from
            the project folder. Defaults to :code:`["input"]`
        :param omp_num_threads: The number of CPU threads to use, defaults to
            {omp_num_threads}
        :param show_stdout: show Delft3D logging to stdout in console, defaults
            to {show_stdout}
        
        :raises OSError: if function is called on an unsupported operating
            system
        :raises FileNotFoundError: if the Delft3D entry point or model folder
            could not be found
        :raises RuntimeError: if the Delft3D simulation outputs to stderr, for
            any reason

        """
        
        if relative_input_parts is None:
            relative_input_parts = ["input"]
        
        if omp_num_threads is None:
            omp_num_threads = self.omp_num_threads
        
        if show_stdout is None:
            show_stdout = self.show_stdout
        
        model_path = Path(project_path).joinpath(*relative_input_parts)
        
        run_dflowfm(self.d3d_bin_path,
                    model_path,
                    omp_num_threads,
                    show_stdout)


@docstringtemplate
def run_dflowfm(d3d_bin_path: StrOrPath,
                model_path: StrOrPath,
                omp_num_threads: int = 1,
                show_stdout: bool = False):
    """Run a Delft3D flexible mesh simulation, given an existing Delft3D
    installation and a prepared model.
    
    Currently only available for Windows and Linux.
    
    :param d3d_bin_path: path to the ``bin`` folder generated when compiling
        Delft3D
    :param model_path: path to folder containing the Delft3D model files
    :param omp_num_threads: The number of CPU threads to use, defaults to
        {omp_num_threads}
    :param show_stdout: show Delft3D logging to stdout in console, defaults to
        {show_stdout}
    
    :raises OSError: if function is called on an unsupported operating system
    :raises FileNotFoundError: if the Delft3D entry point or model folder
        could not be found
    :raises RuntimeError: if the Delft3D simulation outputs to stderr, for any
        reason

    """
    
    dflowfm_entry_point = _get_dflowfm_entry_point(d3d_bin_path)
    
    if not model_path.is_dir():
        raise FileNotFoundError("Model folder could not be found at "
                                f"{model_path}")
    
    env = dict(os.environ)
    env['OMP_NUM_THREADS'] = f"{omp_num_threads}"
    sp = subprocess.Popen([dflowfm_entry_point, "FlowFM.mdu"],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          cwd=model_path,
                          env=env)
    out, err = sp.communicate()
    
    if out and show_stdout:
        print('stdout      :', out.decode('utf-8'))
    
    if err:
        print('stderr      :', err.decode('utf-8'))
        raise RuntimeError("Delft3D simulation failure")


def _get_dflowfm_entry_point(d3d_bin_path: StrOrPath) -> Path:
    
    os_name = platform.system()
    
    # TODO: convert to match-case when 3.10 is supported by deps
    if os_name == 'Windows':
        dflowfm_entry_point = Path(d3d_bin_path).joinpath("x64",
                                                          "dflowfm",
                                                          "scripts",
                                                          "run_dflowfm.bat")
    elif os_name == 'Linux':
        dflowfm_entry_point = Path(d3d_bin_path) / "run_dflowfm.sh"
    else:
        raise OSError(f"Operating system '{os_name}' not supported")
    
    if not dflowfm_entry_point.is_file():
        raise FileNotFoundError("Delft3D script could not be found at "
                                f"{dflowfm_entry_point}")
    
    return dflowfm_entry_point
