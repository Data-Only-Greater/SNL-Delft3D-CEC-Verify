# -*- coding: utf-8 -*-

from typing import Generic, List, TypeVar, Union
from dataclasses import dataclass

# Generics
T = TypeVar("T")


@dataclass
class FixedValue(Generic[T]):
    value: T


@dataclass
class MultiValue(Generic[T]):
    values: List[T]


@dataclass
class TemplateFixedValue(FixedValue[T]):
    pass


@dataclass
class TemplateFMultiValue(MultiValue[T]):
    pass


@dataclass
class CaseStudy:
    """Class for defining cases to test."""
    dx: Union[FixedValue[float], MultiValue[float]] = FixedValue[float](1.)
    dy: Union[FixedValue[float], MultiValue[float]] = FixedValue[float](1.)
    sigma: Union[FixedValue[int], MultiValue[int]] = TemplateFixedValue[int](3)
    discharge: Union[FixedValue[int],
                     MultiValue[int]] = TemplateFixedValue[float](6.0574)

