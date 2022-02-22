# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pathlib import Path
from dataclasses import dataclass

from .types import StrOrPath


@dataclass(frozen=True)
class _BaseModelFinderDataclassMixin:
    project_path: StrOrPath


class _BaseModelFinder(ABC, _BaseModelFinderDataclassMixin):
    
    @property
    @abstractmethod
    def path(self) -> Optional[Path]:
        pass    # pragma: no cover
    
    def is_model(self) -> bool:
        if self.path is None: return False
        return True


# Type variable with an upper bound of _BaseModelFinder
U = TypeVar('U', bound=_BaseModelFinder)


def get_model(project_path: StrOrPath,
              *model_classes: Type[U]) -> Optional[U]:
    
    model = None
    
    for ModelClass in model_classes:
        test_model = ModelClass(project_path)
        if test_model.is_model():
            model = test_model
            break
    
    return model


def find_path(project_path: StrOrPath,
              ext: str,
              partial: Optional[str] = None) -> Optional[Path]:
    
    if partial is None:
        file_root = "*"
    else:
        file_root = f"*{partial}*"
    
    files = list(Path(project_path).glob(f"**/{file_root}{ext}"))
    
    if len(files) > 1:
        msg = f"Multiple files detected with signature '{file_root}{ext}'"
        raise FileNotFoundError(msg)
    
    if not files: return None
    
    return files[0]
