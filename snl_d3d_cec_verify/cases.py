# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Union
from collections.abc import Sequence
from dataclasses import dataclass

from .types import Num

# Reused compound types
OneOrManyNum = Union[Num, Sequence[Num]]


@dataclass
class TemplateValue:
    value: OneOrManyNum
    
    def __format__(self, format_spec):
        return str(self.value)


class CaseStudy:
    """Class for defining cases to test."""
    
    __slots__ = ['_dx', '_dy', '_sigma', '_discharge']
    
    def __init__(self, dx: OneOrManyNum = 1,
                       dy: OneOrManyNum = 1,
                       sigma: OneOrManyNum = 3,
                       discharge: OneOrManyNum = 6.0574):
        
        self._init_check(dx, dy, sigma, discharge)
        
        self._dx: OneOrManyNum = dx
        self._dy: OneOrManyNum = dy
        self._sigma: TemplateValue = TemplateValue(sigma)
        self._discharge: TemplateValue = TemplateValue(discharge)
    
    @property
    def dx(self) -> OneOrManyNum:
        return self._dx
    
    @property
    def dy(self) -> OneOrManyNum:
        return self._dy
    
    @property
    def sigma(self) -> TemplateValue:
        return self._sigma
    
    @property
    def discharge(self) -> TemplateValue:
        return self._discharge
    
    @classmethod
    @property
    def fields(cls) -> List[str]:
        return [x.strip('_') for x in cls.__slots__]
    
    @property
    def values(self) -> List[Union[OneOrManyNum, TemplateValue]]:
        return [getattr(self, x) for x in self.fields]
    
    def get_case(self, index: int = 0) -> CaseStudy:
        
        safe_values = [x.value if isinstance(x, TemplateValue) else x
                                                       for x in self.values]
        
        # All single valued variables, so only 0 and -1 index available
        if len(self) == 1:
            self._single_index_check(index)
            return CaseStudy(*safe_values)
        
        self._multi_index_check(index)
        case_values = [value[index] if isinstance(value, Sequence) else value
                                                   for value in safe_values]
        
        return CaseStudy(*case_values)
    
    def _init_check(self, *args):
        
        mutli_values = {n: v for n, v in zip(self.fields, args)
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
    
    def _single_index_check(self, index: int):
        if index not in [0, -1]: raise IndexError("index out of range")
    
    def _multi_index_check(self, index: int):
        length = len(self)
        if -1 * length > index > length - 1:
            raise IndexError("index out of range")
    
    def __getitem__(self, item: int) -> CaseStudy:
        return self.get_case(item)
    
    def __len__(self) -> int:
        
        safe_values = [x.value if isinstance(x, TemplateValue) else x
                                                       for x in self.values]
        mutli_values = [v for v in safe_values if isinstance(v, Sequence)]
        
        if not mutli_values: return 1
        return len(mutli_values[0])
    
    def __repr__(self) -> str:
        vars_str = [f"{n}={repr(v)}" for n, v in zip(self.fields, self.values)]
        return "CaseStudy({})".format(", ".join(vars_str))
