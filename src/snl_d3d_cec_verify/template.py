# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import tempfile
import platform
from abc import ABCMeta, abstractmethod
from typing import cast, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, InitVar
from distutils.dir_util import copy_tree
from importlib.metadata import version

from .cases import CaseStudy
from .copier import copy_after
from .grid import write_fm_rectangle, write_structured_rectangle
from .types import AnyByStrDict, Num, StrOrPath
from ._docs import docstringtemplate


def package_template_path(template_type) -> Path:
    this_dir = os.path.dirname(os.path.realpath(__file__))
    return Path(this_dir) / "templates" / template_type


@docstringtemplate
@dataclass
class Template:
    """Class for creating Delft3D projects from templates
    
    Utilises the :func:`.copier.copy_after` context manager to fill the
    template and the :func:`.grid.write_fm_rectangle` function to create the 
    flexible mesh grid. Note that the template files are copied on 
    initialization, therefore changes to the template source will not affect 
    the object's output.
    
    Call a Template object with a length one :class:`.CaseStudy` object and
    a path at which to create a Delft3D project. For example:
    
    >>> import pprint
    >>> import tempfile
    >>> from pathlib import Path
    >>> template = Template()
    >>> with tempfile.TemporaryDirectory() as tmpdirname:
    ...     template(CaseStudy(), tmpdirname)
    ...     inputdir = Path(tmpdirname) / "input"
    ...     pprint.pprint(sorted([x.name for x in inputdir.iterdir()]))
    ['Discharge.bc',
     'FlowFM.mdu',
     'FlowFM_bnd.ext',
     'FlowFM_net.nc',
     'Inlet.pli',
     'Outlet.pli',
     'WaterLevel.bc',
     'curves.trb',
     'turbines.ini']
    
    
    :param template_path: path to the Delft3D project template, defaults to
        ``Path("./templates/fm")``
    :param exist_ok: if True, allow an existing path to be overwritten,
        defaults to {exist_ok}
    :param no_template: variables to ignore in the given
        :class:`.CaseStudy` objects when filling templates, defaults to
        ``["dx", "dy"]``
    
    .. automethod:: __call__
    
    """
    
    template_type: InitVar[str] = "fm"
    template_path: InitVar[StrOrPath] = None
    
    #: if True, allow an existing path to be overwritten
    exist_ok: bool = False
    
    #: variables to ignore in the given :class:`.CaseStudy` objects when
    #: filling templates
    no_template: List[str] = field(
                                default_factory=lambda: ["dx",
                                                         "dy",
                                                         "simulate_turbines"])
    
    _template_tmp: tempfile.TemporaryDirectory = field(init=False, repr=False)
    _extras: _BaseTemplateExtras = field(init=False, repr=False)
    
    def __post_init__(self, template_type: str,
                            template_path: StrOrPath):
        
        template_extras_map = {"fm": _FMTemplateExtras,
                               "structured": _StructuredTemplateExtras}
        
        if template_type not in template_extras_map:
            valid_types = ", ".join(template_extras_map)
            msg = f"Template type not recognised. Must be one of {valid_types}"
            raise ValueError(msg)
        
        self._extras = template_extras_map[template_type]()
        
        if template_path is None:
            template_path = package_template_path(template_type)
        
        self._template_tmp = tempfile.TemporaryDirectory()
        copy_tree(str(template_path), self._template_tmp.name)
    
    def __call__(self, case: CaseStudy,
                       project_path: StrOrPath,
                       exist_ok: Optional[bool] = None):
        """Create a new Delft3D project from the given :class:`.CaseStudy`
        object, at the given path.
        
        Note that boolean values are converted to integers and Nones are
        converted to empty strings.
        
        :param case: :class:`.CaseStudy` object from which to build the
            project
        :param project_path: new project destination path
        :param exist_ok: if True, allow an existing path to be overwritten.
            Overrides :attr:`~exist_ok`, if given. 
        
        :raises ValueError: if the given :class:`.CaseStudy` object is not
            length one or if :attr:`~template_path` does not exist
        :raises FileExistsError: if the project path exists, but
            :attr:`~exist_ok` is False
        
        """
        
        if len(case) != 1:
            raise ValueError("case study must have length one")
        
        if exist_ok is None:
            exist_ok = self.exist_ok
        
        # Copy templated files
        data = {field: value
                    for field, value in zip(case.fields, case.values)
                                            if field not in self.no_template}
        
        # Convert booleans to ints
        data = {field: int(value) if type(value) is bool else value
                                        for field, value in data.items()}
        
        # Convert None to ""
        data = {field: "" if value is None else value
                                        for field, value in data.items()}
        
        # Apply template specific updates to the data dictionary
        self._extras.data_hook(case, data)
        
        # Inform the type checker that we have Num for single value cases
        dx = cast(Num, case.dx)
        dy = cast(Num, case.dy)
        x0 = cast(Num, case.x0)
        x1 = cast(Num, case.x1)
        y0 = cast(Num, case.y0)
        y1 = cast(Num, case.y1)
        
        template_path = Path(self._template_tmp.name)
        project_path = Path(project_path)
        
        with copy_after(template_path,
                        project_path,
                        data=data,
                        exist_ok=exist_ok) as data:
            
            grid_data = self._extras.write_grid(project_path,
                                                dx,
                                                dy,
                                                x0,
                                                x1,
                                                y0,
                                                y1)
            data.update(grid_data)
            data["mock"] = "MOCK"


class _BaseTemplateExtras(metaclass=ABCMeta):
    
    @abstractmethod
    def data_hook(self, case: CaseStudy,
                        data: AnyByStrDict):
        pass
    
    @abstractmethod
    def write_grid(self, project_path: StrOrPath,
                         dx: Num,
                         dy: Num,
                         x0: Num,
                         x1: Num,
                         y0: Num,
                         y1: Num) -> AnyByStrDict:
        pass


class _FMTemplateExtras(_BaseTemplateExtras):
    
    def data_hook(self, case: CaseStudy,
                        data: AnyByStrDict):
        
        # Add Turbines section if requested
        if case.simulate_turbines:
            simulate_turbines = (
                "\n"
                "[Turbines]\n"
                "TurbineFile                       = turbines.ini\n"
                "CurvesFile                        = curves.trb")
        else:
            simulate_turbines = ""
        
        data["simulate_turbines"] = simulate_turbines
    
    def write_grid(self, project_path: StrOrPath,
                         dx: Num,
                         dy: Num,
                         x0: Num,
                         x1: Num,
                         y0: Num,
                         y1: Num) -> AnyByStrDict:
        net_path = Path(project_path) / "input" / "FlowFM_net.nc"
        return write_fm_rectangle(net_path, dx, dy, x0, x1, y0, y1)


class _StructuredTemplateExtras(_BaseTemplateExtras):
    
    def data_hook(self, case: CaseStudy,
                        data: AnyByStrDict):
        
        data["date"] = f"{datetime.today().strftime('%Y-%m-%d, %H:%M:%S')}"
        data["version"] = f"{version('SNL-Delft3D-CEC-Verify')}"
        data["os"] = f"{platform.system()}"
        
        if not case.simulate_turbines:
            data["simulate_turbines"] = ""
            return
        
        data["simulate_turbines"] = "Filtrb = #turbines.ini#"
        
        # Inform the type checker that we have Num for single value cases
        dx = cast(Num, case.dx)
        dy = cast(Num, case.dy)
        x0 = cast(Num, case.x0)
        x1 = cast(Num, case.x1)
        y0 = cast(Num, case.y0)
        y1 = cast(Num, case.y1)
        
        # If the turbine position lies on a grid line move it slightly
        xsize = x1 - x0
        ysize = y1 - y0
        
        x, y = generate_grid_xy(x0,
                                y0,
                                xsize,
                                ysize,
                                dx,
                                dy)
        
        micrometre = 1e-6
        
        if np.isclose(case.turb_pos_x, x).any():
            data["turb_pos_x"] += micrometre
        
        if np.isclose(case.turb_pos_y, y).any():
            data["turb_pos_y"] += micrometre
    
    def write_grid(self, project_path: StrOrPath,
                         dx: Num,
                         dy: Num,
                         x0: Num,
                         x1: Num,
                         y0: Num,
                         y1: Num) -> AnyByStrDict:
        return write_structured_rectangle(project_path, dx, dy, x0, x1, y0, y1)
