# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import platform
import subprocess
from abc import abstractmethod
from queue import Queue
from typing import Any, Dict, Iterator, IO, Optional
from pathlib import Path
from threading import Thread
from dataclasses import dataclass

from .types import StrOrPath
from ._docs import docstringtemplate
from ._paths import _BaseModelFinder, find_path, get_model

__all__ = ["run_dflowfm", "run_dflow2d3d"]


@docstringtemplate
@dataclass
class Runner:
    """A class for running Delft3D models which allow reuse of settings across 
    multiple projects. Automatically detects if the model uses a flexible or
    structured mesh and then calls the appropriate function from the 
    :mod:`.runner` package.
    
    Call the Runner object with the project path to execute the Delft3D model
    
    >>> runner = Runner("path/to/Delft3D/src/bin",
    ...                  omp_num_threads=8)
    >>> runner("path/to/project") # doctest: +SKIP
    
    
    Currently only available for Windows and Linux.
    
    :param d3d_bin_path: path to the ``bin`` folder generated when compiling
        Delft3D
    :param omp_num_threads: for ``'fm'`` models, activate parallel computation 
        with the given number of CPU threads, optional
    :param show_stdout: show Delft3D logging to stdout in console, defaults
        to {show_stdout}
    
    .. automethod:: __call__
    
    """
    
    #: path to the ``bin`` folder generated when compiling Delft3D
    d3d_bin_path: StrOrPath
    
    #: The number of CPU threads to use for parallel computation of fm models.
    #: Compuation is serial if None.
    omp_num_threads: Optional[int] = None
    
    show_stdout: bool = False #: show Delft3D logging to stdout in console
    
    def __call__(self, project_path: StrOrPath):
        """
        Run a simulation, given a prepared model.
        
        :param project_path: path to Delft3D project folder 
        
        :raises OSError: if function is called on an unsupported operating
            system
        :raises FileNotFoundError: if the Delft3D entry point or model file
            could not be found (or is not unique)
        :raises RuntimeError: if the Delft3D simulation outputs to stderr, for
            any reason
        
        """
        
        sp = _run_model(project_path,
                        self.d3d_bin_path,
                        omp_num_threads=self.omp_num_threads)
        
        out, err = sp.communicate()
        
        if out and self.show_stdout:
            print('stdout      :', out.decode('utf-8'))
        
        if err:
            print('stderr      :', err.decode('utf-8'))
            raise RuntimeError("Delft3D simulation failure")


@docstringtemplate
@dataclass
class LiveRunner:
    """A class for running Delft3D models which allow reuse of settings across 
    multiple projects with real time output. Automatically detects if the 
    model uses a flexible or structured mesh and then calls the appropriate 
    function from the :mod:`.runner` package.
    
    Call the LiveRunner object with the project path to execute the Delft3D
    model and read the output line by line, like a generator
    
    >>> runner = LiveRunner("path/to/Delft3D/src/bin",
    ...                     omp_num_threads=8)
    >>> for line in runner("path/to/project"): # doctest: +SKIP
    ...     print(line)
    
    
    Currently only available for Windows and Linux.
    
    :param d3d_bin_path: path to the ``bin`` folder generated when compiling
        Delft3D
    :param omp_num_threads: for ``'fm'`` models, activate parallel computation 
        with the given number of CPU threads, optional
    
    .. automethod:: __call__
    
    """
    
    #: path to the ``bin`` folder generated when compiling Delft3D
    d3d_bin_path: StrOrPath
    
    omp_num_threads: int = 1  #: The number of CPU threads to use
    
    def __call__(self, project_path: StrOrPath) -> Iterator[str]:
        """
        Run a simulation, given a prepared model, and yield stdout and stdin
        streams.
        
        :param project_path: path to Delft3D project folder 
        
        :raises OSError: if function is called on an unsupported operating
            system
        :raises FileNotFoundError: if the Delft3D entry point or model file
            could not be found (or is not unique)
        :raises RuntimeError: if the Delft3D simulation outputs to stderr, for
            any reason
        
        """
        
        sp = _run_model(project_path,
                        self.d3d_bin_path,
                        omp_num_threads=self.omp_num_threads)
        
        q: Queue = Queue()
        Thread(target=_pipe_reader, args=[sp.stderr, q]).start()
        Thread(target=_pipe_reader, args=[sp.stdout, q]).start()
        
        stderr = ""
        captured_error = False
        
        for i in range(2):
            
            source: IO
            line: bytes
            
            for source, line in iter(q.get, None): # type: ignore
                
                msg = line.decode('utf-8')
                
                if source == sp.stderr:
                    captured_error = True
                
                yield msg
        
        if captured_error:
            print(stderr)
            raise RuntimeError("Delft3D simulation failure")


def _run_model(project_path: StrOrPath,
               d3d_bin_path: StrOrPath,
               **kwargs: Any) -> subprocess.Popen:
    
    model_runner = get_model(project_path,
                             _FMModelRunner,
                             _StructuredModelRunner)
    
    if model_runner is None:
        msg = "No valid model files detected"
        raise FileNotFoundError(msg)
    
    return model_runner.run_model(d3d_bin_path,
                                  **kwargs)


class _BaseModelRunner(_BaseModelFinder):
    
    @abstractmethod
    def run_model(self, d3d_bin_path: StrOrPath,
                        **kwargs: Any) -> subprocess.Popen:
        pass    # pragma: no cover


class _FMModelRunner(_BaseModelRunner):
    
    @property
    def path(self) -> Optional[Path]:
        return find_path(self.project_path, ".mdu")
    
    def run_model(self, d3d_bin_path: StrOrPath,
                        omp_num_threads: Optional[int] = None,
                        **kwargs: Any) -> subprocess.Popen:
        
        if self.path is None:
            raise FileNotFoundError("No .mdu file detected")
        
        return run_dflowfm(d3d_bin_path,
                           self.path.parent,
                           self.path.name,
                           omp_num_threads)


class _StructuredModelRunner(_BaseModelRunner):
    
    @property
    def path(self) -> Optional[Path]:
        return find_path(self.project_path, ".xml", "config_d_hydro")
    
    def run_model(self, d3d_bin_path: StrOrPath,
                        **kwargs: Any) -> subprocess.Popen:
        
        if self.path is None:
            raise FileNotFoundError("No config_d_hydro.xml file detected")
        
        return run_dflow2d3d(d3d_bin_path,
                             self.path.parent)


@docstringtemplate
def run_dflowfm(d3d_bin_path: StrOrPath,
                model_path: StrOrPath,
                model_file: str,
                omp_num_threads: Optional[int] = None) -> subprocess.Popen:
    """Run a Delft3D flexible mesh simulation, given an existing Delft3D
    installation and a prepared model.
    
    Currently only available for Windows and Linux.
    
    :param d3d_bin_path: path to the ``bin`` folder generated when compiling
        Delft3D
    :param model_path: path to folder containing the Delft3D model files
    :param omp_num_threads: activate parallel computation with the given 
        number of CPU threads, optional
    
    :raises OSError: if function is called on an unsupported operating system
    :raises FileNotFoundError: if the Delft3D entry point or model folder
        could not be found
    :raises RuntimeError: if the Delft3D simulation outputs to stderr, for any
        reason
    
    """
    
    env = None
    
    if omp_num_threads is not None:
        env = dict(os.environ)
        env['OMP_NUM_THREADS'] = f"{omp_num_threads}"
    
    return _run_script("dflowfm",
                       d3d_bin_path,
                       model_path,
                       model_file,
                       env=env)


@docstringtemplate
def run_dflow2d3d(d3d_bin_path: StrOrPath,
                  model_path: StrOrPath) -> subprocess.Popen:
    """Run a Delft3D structured mesh simulation, given an existing Delft3D
    installation and a prepared model.
    
    Currently only available for Windows and Linux.
    
    :param d3d_bin_path: path to the ``bin`` folder generated when compiling
        Delft3D
    :param model_path: path to folder containing the Delft3D model files
    
    :raises OSError: if function is called on an unsupported operating system
    :raises FileNotFoundError: if the Delft3D entry point or model folder
        could not be found
    :raises RuntimeError: if the Delft3D simulation outputs to stderr, for any
        reason
    
    """
    
    return _run_script("dflow2d3d",
                       d3d_bin_path,
                       model_path)


def _run_script(name: str,
                d3d_bin_path: StrOrPath,
                model_path: StrOrPath,
                *args: str,
                env: Optional[Dict[str, str]] = None) -> subprocess.Popen:
    
    if args is None: args = []
    
    entry_point = _get_entry_point(d3d_bin_path, name)
    model_path = Path(model_path)
    
    if not model_path.is_dir():
        raise FileNotFoundError("Model folder could not be found at "
                                f"{model_path}")
    
    if env is None:
        env = dict(os.environ)
    
    popen_args = [str(entry_point.resolve())] + list(args)
    sp = subprocess.Popen(popen_args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          cwd=model_path,
                          env=env)
    
    return sp


def _get_entry_point(d3d_bin_path: StrOrPath,
                     name: str) -> Path:
    
    os_name = platform.system()
    
    if os_name == 'Windows':
        script = "run_" + name + '.bat'
        entry_point = Path(d3d_bin_path).joinpath("x64",
                                                  name,
                                                  "scripts",
                                                  script)
    elif os_name == 'Linux':
        script = "run_" + name + '.sh'
        entry_point = Path(d3d_bin_path) / script
    else:
        raise OSError(f"Operating system '{os_name}' not supported")
    
    if not entry_point.is_file():
        raise FileNotFoundError("Delft3D script could not be found at "
                                f"{entry_point}")
    
    return entry_point


def _pipe_reader(pipe: IO,
                 queue: Queue):
    try:
        with pipe:
            for line in iter(pipe.readline, b''):
                queue.put((pipe, line))
    finally:
        queue.put(None)
