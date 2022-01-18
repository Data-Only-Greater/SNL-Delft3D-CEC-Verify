# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, List, Optional, TypeVar, Union
from collections.abc import Sequence
from dataclasses import dataclass, field, fields

from .types import Num
from ._docs import docstringtemplate

# Reused compound types
T = TypeVar('T')
OneOrMany = Union[T, Sequence[T]]
OneOrManyOptional = Union[Optional[T], Sequence[Optional[T]]]


@docstringtemplate
@dataclass(frozen=True)
class CaseStudy:
    """
    Class for defining variables for single or multiple case studies.
    
    When defining multiple values for multiple variables, the given 
    sequences must be the same length, e.g.:
    
    >>> cases = CaseStudy(dx=[1, 2, 3, 4],
    ...                   dy=[4, 5, 6, 7])
    >>> print(cases) #doctest: +ELLIPSIS
    CaseStudy(dx=[1, 2, 3, 4], dy=[4, 5, 6, 7], sigma=3, ...
    
    The above example will generate an object representing 4 cases, which can
    then be iterated:
    
    >>> for case in cases: #doctest: +ELLIPSIS
    ...     print(case)
    CaseStudy(dx=1, dy=4, ...
    CaseStudy(dx=2, dy=5, ...
    CaseStudy(dx=3, dy=6, ...
    CaseStudy(dx=4, dy=7, ...
    
    :param dx: grid spacing in x-direction, in meters. Defaults to {dx}
    :param dy: grid spacing in y-direction, in meters. Defaults to {dy}
    :param sigma: number of vertical layers, defaults to {sigma}
    :param x0: minimum x-value, in metres, defaults to {x0}
    :param x1: maximum x-value, in metres, defaults to {x1}
    :param y0: minimum y-value, in metres, defaults to {y0}
    :param y1: maximum y-value, in metres, defaults to {y1}
    :param bed_level: uniform bed level, in metres, defaults to {bed_level}
    :param dt_max: maximum time step, in seconds. Defaults to {dt_max}
    :param dt_init: initial time step, in seconds. Defaults to {dt_init}
    :param turb_pos_x: turbine x-position, in meters. Defaults to {turb_pos_x}
    :param turb_pos_y: turbine y-position, in meters. Defaults to {turb_pos_y}
    :param turb_pos_z: turbine z-position, in meters. Defaults to {turb_pos_z}
    :param discharge: inlet boundary discharge, in cubic meters per second.
        Defaults to {discharge}
    :param horizontal_eddy_viscosity: uniform horizontal eddy viscosity, in
        metres squared per second. Defaults to {horizontal_eddy_viscosity}
    :param horizontal_eddy_diffusivity: uniform horizontal eddy diffusivity,
        in metres squared per second. Defaults to {horizontal_eddy_diffusivity}
    :param vertical_eddy_viscosity: uniform vertical eddy viscosity, in
        metres squared per second. Defaults to {horizontal_eddy_viscosity}
    :param vertical_eddy_diffusivity: uniform vertical eddy diffusivity,
        in metres squared per second. Defaults to {vertical_eddy_diffusivity}
    :param simulate_turbines: simulate turbines, defaults to
        {simulate_turbines}
    :param horizontal_momentum_filter: use high-order horizontal momentum 
        filter. Defaults to {horizontal_momentum_filter}
    :param stats_interval: interval for simulation progress output, in seconds
        of simulation time. Defaults to {stats_interval}
    :param restart_interval: interval for restart file output, in seconds of
        simulation time. Defaults to {restart_interval}
    
    :raises ValueError: if variables with multiple values have different
        lengths
    
    """
    
    dx: OneOrMany[Num] = 1 #: grid spacing in x-direction, in meters
    dy: OneOrMany[Num] = 1 #: grid spacing in y-direction, in meters
    sigma: OneOrMany[Num] = 3 #: number of vertical layers
    x0: OneOrMany[Num] = 0 #: minimum x-value, in metres
    x1: OneOrMany[Num] = 18 #: maximum x-value, in metres
    y0: OneOrMany[Num] = 1 #: minimum y-value, in metres
    y1: OneOrMany[Num] = 5 #: maximum y-value, in metres
    bed_level: OneOrMany[Num] = -2 #: uniform bed level, in metres
    dt_max: OneOrMany[Num] = 1 #: maximum time step, in seconds
    dt_init: OneOrMany[Num] = 1 #: initial time step, in seconds
    turb_pos_x: OneOrMany[Num] = 6 #: turbine x-position, in meters
    turb_pos_y: OneOrMany[Num] = 3 #: turbine y-position, in meters
    turb_pos_z: OneOrMany[Num] = -1 #: turbine z-position, in meters
    
    #: inlet boundary discharge, in cubic meters per second
    discharge: OneOrMany[Num] = 6.0574
    
    #: uniform horizontal eddy viscosity, in metres squared per second
    horizontal_eddy_viscosity: OneOrMany[Num] = 1e-06
    
    #: uniform horizontal eddy diffusivity, in metres squared per second
    horizontal_eddy_diffusivity: OneOrMany[Num] = 1e-06
    
    #: uniform vertical eddy viscosity, in metres squared per second
    vertical_eddy_viscosity: OneOrMany[Num] = 1e-06
    
    #: uniform vertical eddy diffusivity, in metres squared per second
    vertical_eddy_diffusivity: OneOrMany[Num] = 1e-06
    
    #: simulate turbines
    simulate_turbines: OneOrMany[bool] = True
    
    #: use high-order horizontal momentum filter
    horizontal_momentum_filter: OneOrMany[bool] = True
    
    #: interval for simulation progress output, in seconds
    stats_interval: OneOrManyOptional[Num] = None
    
    #:interval for restart file output, in seconds
    restart_interval: OneOrMany[Num] = 0
    
    def __post_init__(self):
        
        mutli_values = {n: v for n, v in zip(self.fields, self.values)
                                                if isinstance(v, Sequence)}
        
        # Unpack single length sequences
        for name, value in mutli_values.copy().items():
            if len(value) != 1: continue
            object.__setattr__(self, name, value[0])
            mutli_values.pop(name)
        
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
    def values(self) -> List[Any]:
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
    of :class:`.CaseStudy` with the domain and turbine position fixed.
    
    :param dx: grid spacing in x-directions, in meters. Defaults to {dx}
    :param dy: grid spacing in y-directions, in meters. Defaults to {dy}
    :param sigma: number of vertical layers, defaults to {sigma}
    :param dt_max: maximum time step, in seconds. Defaults to {dt_max}
    :param dt_init: initial time step, in seconds. Defaults to {dt_init}
    :param discharge: inlet boundary discharge, in cubic meters per second.
        Defaults to {discharge}
    :param horizontal_eddy_viscosity: uniform horizontal eddy viscosity, in
        metres squared per second. Defaults to {horizontal_eddy_viscosity}
    :param horizontal_eddy_diffusivity: uniform horizontal eddy diffusivity,
        in metres squared per second. Defaults to {horizontal_eddy_diffusivity}
    :param vertical_eddy_viscosity: uniform vertical eddy viscosity, in
        metres squared per second. Defaults to {horizontal_eddy_viscosity}
    :param vertical_eddy_diffusivity: uniform vertical eddy diffusivity,
        in metres squared per second. Defaults to {vertical_eddy_diffusivity}
    :param simulate_turbines: simulate turbines, defaults to
        {simulate_turbines}
    :param horizontal_momentum_filter: use high-order horizontal momentum 
        filter. Defaults to {horizontal_momentum_filter}
    :param stats_interval: interval for simulation progress output, in seconds
        of simulation time. Defaults to {stats_interval}
    :param restart_interval: interval for restart file output, in seconds of
        simulation time. Defaults to {restart_interval}
    
    :raises ValueError: if variables with multiple values have different
        lengths
    
    """
   
    x0: OneOrMany[Num] = field(default=0, init=False)
    x1: OneOrMany[Num] = field(default=18, init=False)
    y0: OneOrMany[Num] = field(default=1, init=False)
    y1: OneOrMany[Num] = field(default=5, init=False)
    bed_level: OneOrMany[Num] = field(default=-2, init=False)
    turb_pos_x: OneOrMany[Num] = field(default=6, init=False)
    turb_pos_y: OneOrMany[Num] = field(default=3, init=False)
    turb_pos_z: OneOrMany[Num] = field(default=-1, init=False)
