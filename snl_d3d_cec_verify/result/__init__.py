# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import collections
from typing import Dict, Optional, Sequence, TYPE_CHECKING, Union
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from shapely.geometry import LineString

from ..types import Num, StrOrPath


class Result:
    
    def __init__(self, project_path: StrOrPath):
        self.map: xr.Dataset = load_map(project_path)


def load_map(project_path: StrOrPath) -> xr.Dataset:
    map_path = Path(project_path) / "output" / "FlowFM_map.nc"
    return xr.load_dataset(map_path)
