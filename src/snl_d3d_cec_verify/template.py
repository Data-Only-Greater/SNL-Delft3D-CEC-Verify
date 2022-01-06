# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from typing import cast, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

from .cases import CaseStudy
from .copier import copy
from .gridfm import write_gridfm_rectangle
from .types import Num, StrOrPath
from ._docs import docstringtemplate


def package_fm_template_path():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    return Path(this_dir) / "templates" / "fm"


@docstringtemplate
@dataclass
class Template:
    """Class for creating Delft3D projects from templates
    
    Utilises the :func:`.copier.copy` function to fill the template and the
    :func:`.gridfm.write_gridfm_rectangle` function to create the flexible
    mesh grid.
    
    Call a Template object with a length one :class:`.CaseStudy` object and
    a path at which to create a Delft3D project. For example:
    
    >>> import pprint
    >>> import tempfile
    >>> from pathlib import Path
    >>> template = Template()
    >>> with tempfile.TemporaryDirectory() as tmpdirname:
    ...     template(CaseStudy(), tmpdirname)
    ...     inputdir = Path(tmpdirname) / "input"
    ...     pprint.pprint([x.name for x in inputdir.iterdir()])
    ['curves.trb',
     'Discharge.bc',
     'FlowFM.mdu',
     'FlowFM_bnd.ext',
     'FlowFM_net.nc',
     'Inlet.pli',
     'Outlet.pli',
     'turbines.ini',
     'WaterLevel.bc']
    
    
    :param template_path: path to the Delft3D project template, defaults to
        ``Path("./templates/fm")``
    :param exist_ok: if True, allow an existing path to be overwritten,
        defaults to {exist_ok}
    :param no_template: variables to ignore in the given
        :class:`.CaseStudy` objects when filling templates, defaults to
        ``["dx", "dy"]``
    
    .. automethod:: __call__
    
    """
    
    #: path to the Delft3D project template
    template_path: StrOrPath = field(default_factory=package_fm_template_path)
    
    #: if True, allow an existing path to be overwritten
    exist_ok: bool = False
    
    #: variables to ignore in the given :class:`.CaseStudy` objects when
    #: filling templates
    no_template: List[str] = field(default_factory=lambda: ["dx", "dy"])
    
    def __call__(self, case: CaseStudy,
                       project_path: StrOrPath,
                       exist_ok: Optional[bool] = None):
        """Create a new Delft3D project from the given :class:`.CaseStudy`
        object, at the given path.
        
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
        
        template_path = Path(self.template_path)
        project_path = Path(project_path)
        
        # Inform the type checker that we have Num for single value cases
        dx = cast(Num, case.dx)
        dy = cast(Num, case.dy)
        
        copy(template_path, project_path, data=data, exist_ok=exist_ok)
        write_gridfm_rectangle(Path(project_path) / "input" / "FlowFM_net.nc",
                               dx,
                               dy)
