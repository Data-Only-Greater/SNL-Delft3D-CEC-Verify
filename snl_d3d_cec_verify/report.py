# -*- coding: utf-8 -*-

from __future__ import annotations

import textwrap
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass, field


@dataclass
class ParaDataclassMixin:
    line: str
    width: int = field(default=79)


class BaseParagraph(ABC, ParaDataclassMixin):
    
    @abstractmethod
    def wrap(self) -> List[str]:
        pass
    
    def __call__(self, wrap=False):
        
        if wrap:
            line = "\n".join(self.wrap())
        else:
            line = self.line
        
        return line + "\n\n"


class WrappedParagraph(BaseParagraph):
    
    def wrap(self) -> List[str]:
        return textwrap.wrap(self.line, self.width)


class Paragraph(BaseParagraph):
    
    def wrap(self) -> List[str]:
        return [self.line]
