# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Union
from collections.abc import Sequence
from dataclasses import dataclass, field, fields

from .types import Num
from ._docs import docstringtemplate

# Reused compound types
OneOrManyNum = Union[Num, Sequence[Num]]


@docstringtemplate
@dataclass(frozen=True)
class CaseStudy:
    """
    Class for defining single or multiple case studies to test.
    
    When defining multiple values for multiple parameters, the given 
    sequences must be the same length, e.g.:
    
    >>> cases = CaseStudy(dx=[1, 2, 3, 4],
                          dy=[4, 5, 6, 7])
    >>> print(cases)
    CaseStudy(dx=[1, 2, 3, 4], dy=[4, 5, 6, 7], sigma=3, dt_max=1, dt_init=1, \
turb_pos_x=6, turb_pos_y=3, turb_pos_z=-1, discharge=6.0574)
    
    The above example will generate an object representing 4 cases, which can
    then be iterated:
    
    >>> for case in cases:
    ...     print(case)
    CaseStudy(dx=1, dy=4, ...
    CaseStudy(dx=2, dy=5, ...
    CaseStudy(dx=3, dy=6, ...
    CaseStudy(dx=4, dy=7, ...
    
    :param dx: grid spacing in x-directions, in meters. Defaults to {dx}
    :param dy: grid spacing in y-directions, in meters. Defaults to {dy}
    :param sigma: number of vertical layers, defaults to {sigma}
    :param dt_max: maximum time step, in seconds. Defaults to {dt_max}
    :param dt_init: initial time step, in seconds. Defaults to {dt_init}
    :param turb_pos_x: turbine x-position, in meters. Defaults to {turb_pos_x}
    :param turb_pos_y: turbine y-position, in meters. Defaults to {turb_pos_y}
    :param turb_pos_z: turbine z-position, in meters. Defaults to {turb_pos_z}
    :param discharge: inlet boundary discharge, in cubic meters per second.
        Defaults to {discharge}
    """
    
    dx: OneOrManyNum = 1 #: grid spacing in x-directions, in meters
    dy: OneOrManyNum = 1 #: grid spacing in y-directions, in meters
    sigma: OneOrManyNum = 3 #: number of vertical layers,
    dt_max: OneOrManyNum = 1 #: maximum time step, in seconds
    dt_init: OneOrManyNum = 1 #: initial time step, in seconds
    turb_pos_x: OneOrManyNum = 6 #: turbine x-position, in meters
    turb_pos_y: OneOrManyNum = 3 #: turbine y-position, in meters
    turb_pos_z: OneOrManyNum = -1 #: turbine z-position, in meters
    
    #: inlet boundary discharge, in cubic meters per second
    discharge: OneOrManyNum = 6.0574
    
    def __post_init__(self):
        
        mutli_values = {n: v for n, v in zip(self.fields, self.values)
                                                if isinstance(v, Sequence)}
        
        if not mutli_values: return
        
        lengths = {n: len(x) for n, x in mutli_values.items()}
        if len(set(lengths.values())) == 1: return
        
        main_msg = "Multi valued variables have non-equal lengths:\n"
        pad = 8
        
        msgs = []
        for k, v in lengths.items():
            msgs.append(f'{k: >{pad}}: {v}')
        
        main_msg += '\n'.join(msgs)
        
        raise ValueError(main_msg)
    
    @classmethod
    @property
    def fields(cls) -> List[str]:
        """Returns field names"""
        return [x.name for x in fields(cls)]
    
    @property
    def values(self) -> List[OneOrManyNum]:
        """Returns field values"""
        return [getattr(self, f) for f in self.fields]
    
    @docstringtemplate
    def get_case(self, index: int = 0) -> CaseStudy:
        """Return a unit case study, from the given index
        
        :param index: Index of study, defaults to {index}
        """
        
        # All single valued variables, so only 0 and -1 index available
        if len(self) == 1:
            self._single_index_check(index)
            return CaseStudy(*self.values)
        
        self._multi_index_check(index)
        case_values = [value[index] if isinstance(value, Sequence) else value
                                                   for value in self.values]
        
        return CaseStudy(*case_values)
    
    def _single_index_check(self, index: int):
        if index not in [0, -1]: raise IndexError("index out of range")
    
    def _multi_index_check(self, index: int):
        length = len(self)
        if not (-1 * length <= index <= length - 1):
            raise IndexError("index out of range")
    
    def __getitem__(self, item: int) -> CaseStudy:
        return self.get_case(item)
    
    def __len__(self) -> int:
        
        mutli_values = [v for v in self.values if isinstance(v, Sequence)]
        
        if not mutli_values: return 1
        return len(mutli_values[0])


@docstringtemplate
@dataclass(frozen=True)
class MycekStudy(CaseStudy):
    """Class for defining cases corresponding to the Mycek study. Subclass 
    of :class:`.CaseStudy` with the turbine position fixed.
    
    :param dx: grid spacing in x-directions, in meters. Defaults to {dx}
    :param dy: grid spacing in y-directions, in meters. Defaults to {dy}
    :param sigma: number of vertical layers, defaults to {sigma}
    :param dt_max: maximum time step, in seconds. Defaults to {dt_max}
    :param dt_init: initial time step, in seconds. Defaults to {dt_init}
    :param discharge: inlet boundary discharge, in cubic meters per second.
        Defaults to {discharge}
    """
   
    turb_pos_x: OneOrManyNum = field(default=6, init=False)
    turb_pos_y: OneOrManyNum = field(default=3, init=False)
    turb_pos_z: OneOrManyNum = field(default=-1, init=False)
