# -*- coding: utf-8 -*-

from __future__ import annotations

import datetime as dt
import textwrap
from abc import ABC, abstractmethod
from typing import Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class LineDataclassMixin:
    line: str
    width: Optional[int] = field(default=None)


class BaseLine(ABC, LineDataclassMixin):
    
    @abstractmethod
    def wrap(self) -> List[str]:
        pass
    
    def __call__(self):
        
        if self.width is None:
            line = self.line
        else:
            line = "\n".join(self.wrap())
        
        return line + "\n"


class BaseParagraph(BaseLine):
    
    def __call__(self, wrap=False):
        line = super(BaseParagraph, self).__call__(wrap)
        return line + "\n"


class NotWrapped:
    def wrap(self) -> List[str]:
        return [self.line]


class Wrapped:
    def wrap(self) -> List[str]:
        return textwrap.wrap(self.line, self.width)


class Line(NotWrapped, BaseLine):
    pass


class Paragraph(NotWrapped, BaseParagraph):
    pass


class WrappedLine(Wrapped, BaseLine):
    pass


class WrappedParagraph(Wrapped, BaseParagraph):
    pass


class Report:
    
    def __init__(self, width: Optional[int] = None):
        self._title: Optional[Line] = None
        self._authors: Optional[Line] = None
        self._date:  Optional[Line] = None
        self._content: List[Any] = []
        self._width: Optional[int] = width
    
    def set_title(self, text: Optional[str]):
        
        if text is None:
            self._title = None
        else:
            self._title = Line(text, self._width)
    
    def set_authors(self, names: Optional[List[str]]):
        
        if names is None:
            self._authors = None
        else:
            self._authors = Line("; ".join(names), self._width)
    
    def set_date(self, date: Optional[str], format: Optional[str]):
        
        if date is None:
            self._date = None
            return
        
        if date == "today":
            date = dt.date.today()
        else:
            date = dt.date.fromisoformat(date)
        
        if format is None:
            date_str = str(date)
        else:
            date_str = date.strftime(format)
        
        self._date = Line(date_str, width=self._width)
