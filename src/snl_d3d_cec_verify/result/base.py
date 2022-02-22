# -*- coding: utf-8 -*-

from dataclasses import dataclass

from ..types import StrOrPath


@dataclass
class _TimeStepResolver:
    nc_path: StrOrPath #: Path to the `.nc` file containing results
    n_steps: int #: Number of time steps in the simulation
    
    def _resolve_t_step(self, index: int) -> int:
        
        if not (-1 * self.n_steps <= index <= self.n_steps - 1):
            raise IndexError("index out of range")
        
        return index % self.n_steps
