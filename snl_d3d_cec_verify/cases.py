# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Union
from collections.abc import Sequence
from dataclasses import dataclass, fields

from .types import Num

# Reused compound types
OneOrManyNum = Union[Num, Sequence[Num]]


@dataclass(frozen=True)
class CaseStudy:
    """Class for defining cases to test."""
    dx: OneOrManyNum = 1
    dy: OneOrManyNum = 1
    sigma: OneOrManyNum = 3
    dt_max: OneOrManyNum = 1
    dt_init: OneOrManyNum = 1
    turb_pos_x: OneOrManyNum = 6
    turb_pos_y: OneOrManyNum = 3
    turb_pos_z: OneOrManyNum = -1
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
        return [x.name for x in fields(cls)]
    
    @property
    def values(self) -> List[OneOrManyNum]:
        return [getattr(self, f) for f in self.fields]
    
    def get_case(self, index: int = 0) -> CaseStudy:
        
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
