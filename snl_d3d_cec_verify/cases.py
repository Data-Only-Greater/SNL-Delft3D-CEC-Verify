# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Generic, List, TypeVar, Union
from dataclasses import dataclass, fields

# Generics
T = TypeVar("T")


class Template:
    pass


@dataclass
class TemplateValue(Generic[T], Template):
    value: T


@dataclass
class MultiValue(Generic[T]):
    values: List[T]


@dataclass
class TemplateMultiValue(MultiValue[T], Template):
    pass


# Reused compound types
SMFloat = Union[float, MultiValue[float]]
SMInt = Union[int, MultiValue[int]]
TSMFloat = Union[TemplateValue[float], TemplateMultiValue[float]]
TSMInt = Union[TemplateValue[int], TemplateMultiValue[int]]


@dataclass
class CaseStudy:
    """Class for defining cases to test."""
    dx: SMFloat = 1.
    dy: SMFloat = 1.
    sigma: TSMInt = TemplateValue[int](3)
    discharge: TSMFloat = TemplateValue[float](6.0574)
    
    @property
    def fields(self):
        return [x.name for x in fields(self)]
    
    @property
    def values(self):
        return [getattr(self, x) for x in self.fields]
    
    def check(self, quiet: bool=False) -> bool:
        
        mutli_values = {n: dc for n in self.fields
                        if isinstance((dc := getattr(self, n)), MultiValue)}
        
        if not mutli_values: return True
        
        lengths = {n: len(x.values) for n, x in mutli_values.items()}
        
        if len(set(lengths.values())) == 1: return True
        if quiet: return False
        
        main_msg = "Multi valued variables have non-equal lengths:\n"
        pad = 8
        
        msgs = []
        for k, v in lengths.items():
            msgs.append(f'{k: >{pad}}: {v}')
        
        main_msg += '\n'.join(msgs)
        
        raise ValueError(main_msg)
    
    def get_case(self, index: int = -1) -> CaseStudy:
        
        self.check()
        
        mutli_values = {n: dc for n in self.fields
                        if isinstance((dc := getattr(self, n)), MultiValue)}
        
        # All single valued variables, so only 0 and -1 index available
        if not mutli_values:
            if index not in [0, -1]: raise IndexError("index out of range")
            return CaseStudy(*self.values)
        
        length = len(self)
        
        if -1 * length > index > length - 1:
            raise IndexError("index out of range")
        
        new_values = []
        
        # Need to be careful if we need to convert to a TemplateValue
        for i, n in enumerate(self.fields):
            
            if n not in mutli_values:
                new_values.append(self.values[i])
                continue
            
            mutli_value = mutli_values[n]
            value = mutli_value.values[index]
            
            if isinstance(mutli_value, Template):
                value = TemplateValue(value)
            
            new_values.append(value)
        
        return CaseStudy(*new_values)
    
    def __len__(self) -> int:
        
        self.check()
        
        mutli_values = [dc for n in self.fields
                        if isinstance((dc := getattr(self, n)), MultiValue)]
        
        if not mutli_values: return 1
        return len(mutli_values[0].values)
