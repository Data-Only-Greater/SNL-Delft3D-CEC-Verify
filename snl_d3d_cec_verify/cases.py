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


@dataclass(init=False)
class MultiValue(Generic[T]):
    values: List[T]
    
    def __init__(self, *args: T):
        self.values = list(args)


@dataclass(init=False)
class TemplateMultiValue(MultiValue[T], Template):
    
    def __init__(self, *args: T):
        self.values = list(args)


# Reused compound types
SMFloat = Union[float, MultiValue[float], None]
SMInt = Union[int, MultiValue[int], None]
TSMFloat = Union[TemplateValue[float], TemplateMultiValue[float], None]
TSMInt = Union[TemplateValue[int], TemplateMultiValue[int], None]


@dataclass
class CaseStudy:
    """Class for defining cases to test."""
    dx: SMFloat = 1.
    dy: SMFloat = 1.
    sigma: TSMInt = TemplateValue[int](3)
    discharge: TSMFloat = TemplateValue[float](6.0574)
    
    def __post_init__(self):
        self._init_check()
    
    @classmethod
    @property
    def fields(cls):
        return [x.name for x in fields(cls)]
    
    @property
    def values(self):
        return [getattr(self, x) for x in self.fields]
    
    @property
    def empty(self):
        return not bool(len(self))
    
    def nullify(self):
        for name in self.fields:
            setattr(self, name, None)
    
    def get_case(self, index: int = 0) -> CaseStudy:
        
        mutli_values = {n: v for n, v in zip(self.fields, self.values)
                                                if isinstance(v, MultiValue)}
        
        # All single valued variables, so only 0 and -1 index available
        if not mutli_values:
            self._single_index_check(index)
            return CaseStudy(*self.values)
        
        self._multi_index_check(index)
        
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
    
    def remove_case(self, index: int = 0):
        
        if self.empty:
            raise IndexError("remove from empty study")
        
        mutli_values = {n: v for n, v in zip(self.fields, self.values)
                                                if isinstance(v, MultiValue)}
        
        # All single valued variables, so only 0 and -1 index available
        if not mutli_values:
            self._single_index_check(index)
            self.nullify()
            return
        
        self._multi_index_check(index)
        
        if len(self) > 2:
            for name, mutli_value in mutli_values.items():
                mutli_value.values.pop(index)
            return
        
        # Switching to single value types
        for name, mutli_value in mutli_values.items():
            
            mutli_value.values.pop(index)
            new_value = mutli_value.values[0]
            
            if isinstance(mutli_value, Template):
                setattr(self, name, TemplateValue(new_value))
            else:
                setattr(self, name, new_value)
    
    def pop_case(self, index: int = 0) -> CaseStudy:
        
        if self.empty:
            raise IndexError("pop from empty study")
        
        case = self.get_case(index)
        self.remove_case(index)
        
        return case
    
    def _init_check(self):
        
        check_nones = tuple(x is None for x in self.values)
        
        if 0 < sum(check_nones) < len(self.fields):
            raise ValueError("None may only be used to initialise all values")
        
        mutli_values = {n: v for n, v in zip(self.fields, self.values)
                                                if isinstance(v, MultiValue)}
        
        if not mutli_values:
            check_nones = tuple(x for x in range(10))
            
            
            return
        
        lengths = {n: len(x.values) for n, x in mutli_values.items()}
        
        if len(set(lengths.values())) == 1: return
        
        main_msg = "Multi valued variables have non-equal lengths:\n"
        pad = 8
        
        msgs = []
        for k, v in lengths.items():
            msgs.append(f'{k: >{pad}}: {v}')
        
        main_msg += '\n'.join(msgs)
        
        raise ValueError(main_msg)
    
    def _single_index_check(self, index: int):
        if index not in [0, -1]: raise IndexError("index out of range")
    
    def _multi_index_check(self, index: int):
        length = len(self)
        if -1 * length > index > length - 1:
            raise IndexError("index out of range")
    
    def __len__(self) -> int:
        
        if all(x is None for x in self.values): return 0
        
        mutli_values = [v for n, v in zip(self.fields, self.values)
                                                if isinstance(v, MultiValue)]
        
        if not mutli_values: return 1
        return len(mutli_values[0].values)
