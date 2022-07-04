# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Iterable, List, Optional, Type, TypeVar, Union
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, fields

from yaml import load, dump
try:
    from yaml import CSafeLoader as Loader, CSafeDumper as Dumper
except ImportError: # pragma: no cover
    from yaml import SafeLoader as Loader, SafeDumper as Dumper # type: ignore

from .types import Num, StrOrPath
from ._docs import docstringtemplate

# Reused compound types
T = TypeVar('T')
OneOrMany = Union[T, Sequence[T]]
OneOrManyOptional = Union[Optional[T], Sequence[Optional[T]]]

# Create a generic variable that can be 'CaseStudy', or any subclass.
C = TypeVar('C', bound='CaseStudy')


@docstringtemplate
@dataclass(eq=False, frozen=True)
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
    :param dt_max: maximum time step, in seconds. Applies to the ``'fm'``
        model only. Defaults to {dt_max}
    :param dt_init: initial time step, in seconds. For the ``'structured'``
        model, this is the fixed time step. Defaults to {dt_init}
    :param turb_pos_x: turbine x-position, in meters. Defaults to {turb_pos_x}
    :param turb_pos_y: turbine y-position, in meters. Defaults to {turb_pos_y}
    :param turb_pos_z: turbine z-position, in meters. Defaults to {turb_pos_z}
    :param discharge: inlet boundary discharge, in cubic meters per second.
        Defaults to {discharge}
    :param bed_roughness: uniform bed roughness coefficient, as a Manning 
        number, in seconds over metres cube rooted. Defaults to {bed_roughness}
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
    :param turbine_turbulence_model: turbine turbulence model. Set to 
        ``'delft'`` for the default model or ``'canopy'`` to use the 
        Réthoré (2009) canopy model. Defaults to {turbine_turbulence_model}
    :param beta_p: turbine turbulence canopy model "production" coefficient, 
        :math:`\\beta_p`. Applies to the ``'canopy'`` turbine turbulence model 
        only. Defaults to {beta_p}.
    :param beta_d: turbine turbulence canopy model "dissipation" coefficient, 
        :math:`\\beta_d`. Applies to the ``'canopy'`` turbine turbulence model 
        only. Defaults to {beta_d}.
    :param c_epp: turbine turbulence canopy model "production" closure 
        coefficient, :math:`C_{{\\varepsilon p}}`. Applies to the 
        ``'canopy'`` turbine turbulence model only. Defaults to {c_epp}.
    :param c_epd: turbine turbulence canopy model "dissipation" closure 
        coefficient, :math:`C_{{\\varepsilon d}}`. Applies to the 
        ``'canopy'`` turbine turbulence model only. Defaults to {c_epd}.
    :param horizontal_momentum_filter: use high-order horizontal momentum 
        filter. Applies to the ``'fm'`` model only. Defaults to 
        {horizontal_momentum_filter}
    :param stats_interval: interval for simulation progress output, in seconds
        of simulation time. Applies to the ``'fm'`` model only. Defaults to 
        {stats_interval}
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
    
    #: maximum time step, in seconds. Applies to the ``'fm'`` model only
    dt_max: OneOrMany[Num] = 1
    
    #: initial time step, in seconds. For the ``'structured'`` model, this 
    #: is the fixed time step
    dt_init: OneOrMany[Num] = 1
    
    turb_pos_x: OneOrMany[Num] = 6 #: turbine x-position, in meters
    turb_pos_y: OneOrMany[Num] = 3 #: turbine y-position, in meters
    turb_pos_z: OneOrMany[Num] = -1 #: turbine z-position, in meters
    
    #: inlet boundary discharge, in cubic meters per second
    discharge: OneOrMany[Num] = 6.0574
    
    #: uniform bed roughness coefficient, as a Manning number, in seconds
    #: over metres cube rooted
    bed_roughness: OneOrMany[Num] = 0.023
    
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
    
    #: turbine turbulence model. Set to ``'delft'`` for the default model or
    #: ``'canopy'`` to use the Réthoré (2009) canopy model.
    turbine_turbulence_model: OneOrMany[str] = 'delft'
    
    #: turbine turbulence canopy model "production" coefficient, 
    #: :math:`\beta_p`. Applies to the ``'canopy'`` turbine turbulence model 
    #: only.
    beta_p: OneOrMany[Num] = 1.
    
    #: turbine turbulence canopy model "dissipation" coefficient, 
    #: :math:`\beta_d`. Applies to the ``'canopy'`` turbine turbulence model 
    #: only.
    beta_d: OneOrMany[Num] = 1.84
    
    #: turbine turbulence canopy model "production" closure coefficient, 
    #: :math:`C_{\varepsilon p}`. Applies to the ``'canopy'`` turbine 
    #: turbulence model only.
    c_epp: OneOrMany[Num] =  0.77
    
    #: turbine turbulence canopy model "dissipation" closure coefficient, 
    #: :math:`C_{\varepsilon d}`. Applies to the ``'canopy'`` turbine 
    #: turbulence model only.
    c_epd: OneOrMany[Num] = 0.13
    
    #: use high-order horizontal momentum filter. Applies to the ``'fm'`` 
    #: model only
    horizontal_momentum_filter: OneOrMany[bool] = True
    
    #: interval for simulation progress output, in seconds. Applies to the 
    #: ``'fm'`` model only
    stats_interval: OneOrManyOptional[Num] = None
    
    #:interval for restart file output, in seconds
    restart_interval: OneOrMany[Num] = 0
    
    def __post_init__(self):
        
        mutli_values = {n: v for n, v in zip(self.fields, self.values)
                                                        if is_sequence(v)}
        
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
        case_values = [value[index] if is_sequence(value) else value
                                                   for value in self.values]
        
        return CaseStudy(*case_values)
    
    @classmethod
    def from_yaml(cls: Type[C], path: StrOrPath) -> C:
        """Create a new instance from a YAML file
        
        :param path: path of the existing YAML file
        """
        
        with open(path, 'r') as yamlfile:
            raw = load(yamlfile, Loader=Loader)
        
        kwarg_names = [f.name for f in fields(cls) if f.init]
        kwargs = {key: raw[key] for key in kwarg_names}
        
        return cls(**kwargs)
    
    def to_yaml(self, path: StrOrPath):
        """Export object as a YAML file
        
        :param path: path of created YAML file
        """
        
        data = asdict(self)
        
        with open(path, 'w') as yamlfile:
            dump(data, yamlfile, Dumper=Dumper)
    
    def is_equal(self, other: object,
                       ignore_fields: Optional[Iterable[str]] = None) -> bool:
        """Test equality of another object
        
        Use the ``ignore_fields`` argument to ignore fields when comparing
        :class:`.CaseStudy` objects:
        
        >>> case = CaseStudy(dx=1)
        >>> other = CaseStudy(dx=2)
        >>> other.is_equal(case, ignore_fields=["dx"])
        True
        
        :param other: the object to test for equality
        :param ignore_fields: a sequence of field names to ignore
        """
        
        if not isinstance(other, CaseStudy):
            return NotImplemented
        
        if ignore_fields is None: ignore_fields = []
        other_dict = asdict(other)
        
        for f, v in zip(self.fields, self.values):
            
            if f in ignore_fields: continue
            
            other_v = other_dict[f]
            
            if is_sequence(v):
                if tuple(v) != tuple(other_v): return False
            else:
                if v != other_v: return False
        
        return True
    
    def _single_index_check(self, index: int):
        if index not in [0, -1]: raise IndexError("index out of range")
    
    def _multi_index_check(self, index: int):
        length = len(self)
        if not (-1 * length <= index <= length - 1):
            raise IndexError("index out of range")
    

    
    def __eq__(self, other: object) -> bool:
        return self.is_equal(other)
    
    def __getitem__(self, item: int) -> CaseStudy:
        return self.get_case(item)
    
    def __len__(self) -> int:
        
        mutli_values = [v for v in self.values if is_sequence(v)]
        
        if not mutli_values: return 1
        return len(mutli_values[0])


def is_sequence(x):
    return isinstance(x, Sequence) and not isinstance(x, str)


@docstringtemplate
@dataclass(eq=False, frozen=True)
class MycekStudy(CaseStudy):
    """Class for defining cases corresponding to the Mycek study. Subclass 
    of :class:`.CaseStudy` with the domain and turbine position fixed.
    
    :param dx: grid spacing in x-directions, in meters. Defaults to {dx}
    :param dy: grid spacing in y-directions, in meters. Defaults to {dy}
    :param sigma: number of vertical layers, defaults to {sigma}
    :param dt_max: maximum time step, in seconds. Applies to the ``'fm'``
        model only. Defaults to {dt_max}
    :param dt_init: initial time step, in seconds. For the ``'structured'``
        model, this is the fixed time step. Defaults to {dt_init}
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
        filter. Applies to the ``'fm'`` model only. Defaults to 
        {horizontal_momentum_filter}
    :param stats_interval: interval for simulation progress output, in seconds
        of simulation time. Applies to the ``'fm'`` model only. Defaults to 
        {stats_interval}
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
