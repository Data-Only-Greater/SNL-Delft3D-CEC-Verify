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


def package_fm_template_path():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    return Path(this_dir) / "templates" / "fm"


@dataclass
class Template:
    template_path: StrOrPath = field(default_factory=package_fm_template_path)
    exist_ok: bool = False
    no_template: List[str] = field(default_factory=lambda: ["dx", "dy"])
    
    def __call__(self, case: CaseStudy,
                       project_path: StrOrPath,
                       exist_ok: Optional[bool] = None):
        
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
