# -*- coding: utf-8 -*-

from __future__ import annotations

import datetime as dt
import textwrap
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Type
from pathlib import Path
from dataclasses import dataclass, field

import pandas as pd # type: ignore

from .types import StrOrPath
from ._docs import docstringtemplate

__all__ = ["Content"]


@dataclass
class _TextDataclassMixin:
    text: str
    width: Optional[int] = field(default=None)


class _BaseLine(ABC, _TextDataclassMixin):
    
    @abstractmethod
    def wrap(self) -> List[str]:
        pass    # pragma: no cover
    
    def __call__(self):
        return "\n".join(self.wrap())


class _BaseParagraph(_BaseLine):
    
    def __call__(self):
        line = super(_BaseParagraph, self).__call__()
        return line + "\n"


class _Line(_BaseLine):
    def wrap(self) -> List[str]:
        return [self.text]


class _Paragraph(_BaseParagraph):
    def wrap(self) -> List[str]:
        return [self.text]


class _WrappedLine(_BaseLine):
    def wrap(self) -> List[str]:
        if self.width is None:
            return [self.text]
        return textwrap.wrap(self.text, self.width)


class _WrappedParagraph(_BaseParagraph):
    def wrap(self) -> List[str]:
        if self.width is None:
            return [self.text]
        return textwrap.wrap(self.text, self.width)


@dataclass
class _MetaLine:
    line: Optional[_Line] = field(default=None, init=False)
    
    @property
    def defined(self):
        return self.line is not None
    
    def add_line(self, text: Optional[str] = None):
        if text is None:
            self.line = None
        else:
            self.line = _Line(text)
    
    def __call__(self):
        
        if self.defined:
            return "% " + self.line()
        
        return "%"


@dataclass
class Content:
    """Class for storing document content in Pandoc markdown format. Use in
    conjunction with the :class:`.Report` class.
    
    Content is stored in order, for example:
    
    >>> report = Report()
    >>> report.content.add_text("one")
    >>> report.content.add_text("two")
    >>> print(report)
    1: one
    2:
    3: two
    4:
    
    Note that an empty line is placed between each part of the content.
    
    :param width: maximum paragraph width, in characters
    """
    
    #: maximum paragraph width, in characters
    width: Optional[int] = field(default=None)
    _body: List[Tuple[str, Type[_BaseParagraph]]] = field(default_factory=list,
                                                          init=False)
    
    @docstringtemplate
    def add_text(self, text: str, wrapped: bool = True):
        """Add a paragraph of text to the document.
        
        >>> report = Report()
        >>> report.content.add_text("one")
        >>> print(report)
        1: one
        2:
        
        :param text: Paragraph text
        :param wrapped: Wrap the text based on the value of the :attr:`width`
            parameter, defaults to {wrapped}.
        
        """
        
        if wrapped:
            self._body.append((text, _WrappedParagraph))
        else:
            self._body.append((text, _Paragraph))
    
    @docstringtemplate
    def add_heading(self, text: str, level: int = 1):
        """Add a heading to the document.
        
        >>> report = Report()
        >>> report.content.add_heading("One")
        >>> print(report)
        1: # One
        2:
        
        :param text: Heading text
        :param level: Heading level, defaults to {level}.
        
        """
        
        start = '#' * level + ' '
        self.add_text(start + text, wrapped=False)
    
    @docstringtemplate
    def add_table(self, dataframe: pd.DataFrame,
                        index: bool = True,
                        caption: Optional[str] = None):
        """Add a table to the document, converted from a 
        :class:`pandas:pandas.DataFrame`.
        
        >>> report = Report()
        >>> a = {{"a": [1, 2],
        ...      "b": [3, 4]}}
        >>> df = pd.DataFrame(a)
        >>> report.content.add_table(df, index=False, caption="A table")
        >>> print(report)
        1: |   a |   b |
        2: |----:|----:|
        3: |   1 |   3 |
        4: |   2 |   4 |
        5:
        6: Table:  A table
        7:
        
        :param dataframe: DataFrame containing the table headings and data 
        :param index: include the DataFrame index in the table, defaults to
            {index}
        :param caption: add a caption for the table

        """
        
        self.add_text(dataframe.to_markdown(index=index), wrapped=False)
        
        if caption is None: return
        
        text = "Table:  " + caption
        self.add_text(text, wrapped=False)
    
    def add_image(self, path: StrOrPath,
                        caption: Optional[str] = None,
                        width: Optional[str] = None,
                        height: Optional[str] = None):
        """Add image to document, passed as path to a compatible image file.
        
        >>> report = Report()
        >>> report.content.add_image("high_art.png",
        ...                          caption="Probably an NFT",
        ...                          width="6in",
        ...                          height="4in")
        >>> print(report)
        1: ![Probably an NFT](high_art.png){ width=6in height=4in }
        2:
        
        :param path: path to the image file
        :param caption: caption for the image
        :param width: image width in document, including units
        :param height: image height in document, including units

        """
        
        path = Path(path)
        
        if caption is None:
            text = f"![{path}]"
        else:
            text = f"![{caption}]"
        
        text += f"({path})"
        
        if width is not None or height is not None:
            
            attrs_str = "{ "
            
            if width is not None:
                attrs_str += f"width={width} "
            
            if height is not None:
                attrs_str += f"height={height} "
            
            attrs_str += "}"
            text += attrs_str
        
        if caption is None: text += "\\"
        
        self.add_text(text, wrapped=False)
    
    def clear(self):
        """Remove all content from the document
        
        >>> report = Report()
        >>> report.content.add_text("one")
        >>> report.content.add_text("two")
        >>> report.content.clear()
        >>> print(report)
        
        
        """
        
        self._body = []
    
    def undo(self):
        """Undo the last content addition
        
        >>> report = Report()
        >>> report.content.add_text("one")
        >>> report.content.add_text("two")
        >>> report.content.undo()
        >>> print(report)
        1: one
        2:
        
        """
        
        self._body.pop()
    
    def __call__(self) -> List[str]:
        
        parts = []
        
        for text, Para in self._body:
            part = Para(text, self.width)
            parts.append(part())
        
        return parts


class Report:
    """Class for creating a report in Pandoc markdown format
    
    The final report can be viewed by printing the Report object, for example:
    
    >>> report = Report(70, "%d %B %Y")
    >>> report.title = "Test"
    >>> report.authors = ["Me", "You"]
    >>> report.date = "1916-04-24"
    >>> report.content.add_text("Lorem ipsum dolor sit amet, consectetur "
    ...                         "adipiscing elit. Maecenas vitae "
    ...                         "scelerisque magna.")
    >>> print(report)
    1: % Test
    2: % Me; You
    3: % 24 April 1916
    4:
    5: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas
    6: scelerisque magna.
    7:
    
    Note that line numbers are also printed. The report can also be saved to
    file, by iterating through each line:
    
    >>> with open("report.md", "wt") as f:
    ...     for line in report:
    ...         f.write(line)
    
    :param width: maximum paragraph width, in characters
    :param date_format: format for document date as passed to 
        :py:meth:`datetime.date.strftime()`
    """
    
    def __init__(self, width: Optional[int] = None,
                       date_format: Optional[str] = None):
        self._width = width
        self._date_format = date_format
        self._meta: List[_MetaLine] = [_MetaLine() for _ in range(3)]
        self._date: Optional[dt.date] = None
        
        #: Container for the main body of the document. See the 
        #: :class:`.Content` documentation for usage.
        self.content: Content = Content(width)
    
    @property
    def width(self):
        """The maximum paragraph width, in characters. Set to None for no
        limit.
        
        :type: Optional[int]
        """
        return self._width
    
    @width.setter
    def width(self, value: Optional[int]):
        self._width = value
        self.content.width = value
    
    @property
    def date_format(self):
        """format for document date as passed to 
        :py:meth:`datetime.date.strftime()`. Set to None to use ISO 8601 format
        
        :type: Optional[str]
        """
        return self._date_format
    
    @date_format.setter
    def date_format(self, text: Optional[str]):
        self._date_format = text
        if self._date is None: return
        self.date = str(self._date)
    
    @property
    def title(self):
        """Title for the document. Set to None to remove.
        
        :type: Optional[str]
        """
        return self._get_meta_text(0)
    
    @title.setter
    def title(self, text: Optional[str]):
        if text is None:
            self._meta[0].add_line()
        else:
            self._meta[0].add_line(text)
    
    @property
    def authors(self):
        """The authors of the document, as a list. Set to None to remove.
        
        :type: Optional[List[str]]
        """
        return self._get_meta_text(1)
    
    @authors.setter
    def authors(self, names: Optional[List[str]]):
        if names is None:
            self._meta[1].add_line()
        else:
            self._meta[1].add_line("; ".join(names))
    
    @property
    def date(self):
        """The date of the document. Can be set using ISO 8601 format or can
        be given as "today" to use the current date. Set to None to remove.
        
        :type: Optional[str]
        
        """
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
