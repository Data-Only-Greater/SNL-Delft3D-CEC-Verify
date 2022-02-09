# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import tempfile
from typing import cast, List, Optional
from pathlib import Path
from dataclasses import dataclass, field, InitVar
from distutils.dir_util import copy_tree

from .cases import CaseStudy
from .copier import copy
from .grid import write_fm_rectangle
from .types import Num, StrOrPath
from ._docs import docstringtemplate


def package_fm_template_path() -> Path:
    this_dir = os.path.dirname(os.path.realpath(__file__))
    return Path(this_dir) / "templates" / "fm"


@docstringtemplate
@dataclass
class Template:
    """Class for creating Delft3D projects from templates
    
    Utilises the :func:`.copier.copy` function to fill the template and the
    :func:`.gridfm.write_gridfm_rectangle` function to create the flexible
    mesh grid. Note that the template files are copied on initialization,
    therefore changes to the template source will not affect the object's
    output.
    
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
    
    def __post_init__(self, template_path: StrOrPath):
        
        if template_path is None:
            template_path = package_fm_template_path()
        
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
        
        template_path = Path(self._template_tmp.name)
        project_path = Path(project_path)
        
        # Inform the type checker that we have Num for single value cases
        dx = cast(Num, case.dx)
        dy = cast(Num, case.dy)
        x0 = cast(Num, case.x0)
        x1 = cast(Num, case.x1)
        y0 = cast(Num, case.y0)
        y1 = cast(Num, case.y1)
        
        copy(template_path, project_path, data=data, exist_ok=exist_ok)
        write_fm_rectangle(Path(project_path) / "input" / "FlowFM_net.nc",
                           dx,
                           dy,
                           x0,
                           x1,
                           y0,
                           y1)
