# -*- coding: utf-8 -*-

from __future__ import annotations

import datetime as dt
import textwrap
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Type, TYPE_CHECKING, Union
from pathlib import Path
from dataclasses import dataclass, field

from .types import StrOrPath

if TYPE_CHECKING:
    import pandas as pd # type: ignore


@dataclass
class TextDataclassMixin:
    text: str
    width: Optional[int] = field(default=None)


class BaseLine(ABC, TextDataclassMixin):
    
    @abstractmethod
    def wrap(self) -> List[str]:
        pass
    
    def __call__(self):
        return "\n".join(self.wrap())


class BaseParagraph(BaseLine):
    
    def __call__(self):
        line = super(BaseParagraph, self).__call__()
        return line + "\n"


class Line(BaseLine):
    def wrap(self) -> List[str]:
        return [self.text]


class Paragraph(BaseParagraph):
    def wrap(self) -> List[str]:
        return [self.text]


class WrappedLine(BaseLine):
    def wrap(self) -> List[str]:
        if self.width is None:
            return [self.text]
        return textwrap.wrap(self.text, self.width)


class WrappedParagraph(BaseParagraph):
    def wrap(self) -> List[str]:
        if self.width is None:
            return [self.text]
        return textwrap.wrap(self.text, self.width)


@dataclass
class MetaLine:
    line: Optional[Line] = field(default=None, init=False)
    
    @property
    def defined(self):
        return self.line is not None
    
    def add_line(self, text: Optional[str] = None):
        if text is None:
            self.line = None
        else:
            self.line = Line(text)
    
    def __call__(self):
        
        if self.defined:
            return "% " + self.line()
        
        return "%"


@dataclass
class Content:
    width: Optional[int] = field(default=None)
    body: List[Tuple[str, Type[BaseParagraph]]] = field(default_factory=list,
                                                        init=False)
    
    def clear(self):
        self.body = []
    
    def undo(self):
        self.body.pop()
    
    def add_text(self, text: str, wrapped: bool = True):
        
        if wrapped:
            self.body.append((text, WrappedParagraph))
        else:
            self.body.append((text, Paragraph))
    
    def add_heading(self, text: str, level: int = 1):
        start = '#' * level + ' '
        self.add_text(start + text, wrapped=False)
    
    def add_table(self, dataframe: pd.DataFrame,
                        index: bool = True,
                        caption: Optional[str] = None):
        
        self.add_text(dataframe.to_markdown(index=index), wrapped=False)
        
        if caption is None: return
        
        text = "Table:  " + caption
        self.add_text(text, wrapped=False)
    
    def add_image(self, path: StrOrPath,
                        caption: Optional[str] = None):
        
        path = Path(path)
        
        if caption is None:
            text = f"![{path}]"
        else:
            text = f"![{caption}]"
        
        text += f"({path})"
        if caption is None: text += "\\"
        
        self.add_text(text, wrapped=False)
    
    def __call__(self) -> List[str]:
        
        parts = []
        
        for text, Para in self.body:
            part = Para(text, self.width)
            parts.append(part())
        
        return parts


class Report:
    
    def __init__(self, width: Optional[int] = None,
                       date_format: Optional[str] = None):
        self._width = width
        self._date_format = date_format
        self._meta: List[MetaLine] = [MetaLine() for _ in range(3)]
        self._date: Optional[dt.date] = None
        self.content: Content = Content(width)
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value: Optional[int]):
        self._width = value
        self.content.width = value
    
    @property
    def date_format(self):
        return self._date_format
    
    @date_format.setter
    def date_format(self, text: str):
        self._date_format = text
        if self._date is None: return
        self.date = str(self._date)
    
    @property
    def title(self):
        return self._get_meta_text(0)
    
    @title.setter
    def title(self, text: Optional[str]):
        if text is None:
            self._meta[0].add_line()
        else:
            self._meta[0].add_line(text)
    
    @property
    def authors(self):
        return self._get_meta_text(1)
    
    @authors.setter
    def authors(self, names: Optional[List[str]]):
        if names is None:
            self._meta[1].add_line()
        else:
            self._meta[1].add_line("; ".join(names))
    
    @property
    def date(self):
        return self._get_meta_text(2)
    
    @date.setter
    def date(self, date: Optional[str]):
        
        if date is None:
            self._meta[2].add_line()
            self._date = None
            return
        
        if date == "today":
            self._date = dt.date.today()
        else:
            self._date = dt.date.fromisoformat(date)
        
        if self._date_format is None:
            date_str = str(self._date)
        else:
            date_str = self._date.strftime(self.date_format)
        
        self._meta[2].add_line(date_str)
    
    def _get_meta_text(self, index: int) -> Optional[str]:
        
        meta_line = self._meta[index].line
        
        if meta_line is not None:
            return meta_line.text
        
        return None
    
    def _get_meta(self) -> List[str]:
        
        max_rank = -1
        
        for i, meta in enumerate(self._meta):
            if meta.defined: max_rank = i
        
        if max_rank < 0: return []
        
        lines = []
        
        for meta in self._meta[:max_rank + 1]:
            lines.append(meta())
        
        return lines + [""]
    
    def _parts_to_lines(self):
        
        parts = self._get_meta() + self.content()
        lines = []
        
        for part in parts:
            part_lines = part.split("\n")
            lines += [p + "\n" for p in part_lines]
        
        return lines
    
    def __getitem__(self, index: int) -> List[str]:
        lines = self._parts_to_lines()
        return lines[index]
    
    def __iter__(self):
        lines = self._parts_to_lines()
        return iter(lines)
    
    def __len__(self) -> int:
        lines = self._parts_to_lines()
        return len(lines)

    def __repr__(self) -> str:
        
        repr_str = "Report("
        arg_strs = []
        
        if self.width is not None:
            arg_strs.append(f"width={self.width}")
        
        if self.date_format is not None:
            arg_strs.append(f"date_format={self.date_format}")
        
        if self.title is not None:
            arg_strs.append(f"title={self.title}")
        
        if self.authors is not None:
            arg_strs.append(f"authors={self.authors}")
        
        if self.date is not None:
            arg_strs.append(f"date={self._date}")
        
        repr_str += ", ".join(arg_strs) + ")"
        
        return repr_str
    
    def __str__(self) -> str:
        
        lines = []
        number_width = len(str(len(self)))
        
        for i, part in enumerate(self):
            lines.append(f"{i+1:>{number_width}}: {part}")
        
        return "".join(lines)
