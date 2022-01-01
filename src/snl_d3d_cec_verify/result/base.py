# -*- coding: utf-8 -*-

from dataclasses import dataclass

from ..types import StrOrPath


@dataclass
class TimeStepResolver:
    map_path: StrOrPath     # Needs to go here for order in subclasses
    n_steps: int
    
    def _resolve_t_step(self, index: int) -> int:
        
        if not (-1 * self.n_steps <= index <= self.n_steps - 1):
            raise IndexError("index out of range")
        
        return index % self.n_steps
