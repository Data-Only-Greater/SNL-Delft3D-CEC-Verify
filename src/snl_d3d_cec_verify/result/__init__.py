# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import csv
import itertools
from abc import abstractmethod
from typing import (Any,
                    Hashable,
                    List,
                    Mapping,
                    Optional,
                    Tuple,
                    Type,
                    TypeVar,
                    Union)
from pathlib import Path
from collections import defaultdict
from collections.abc import KeysView, Sequence
from dataclasses import dataclass, field, InitVar

import numpy as np
import xarray as xr
import numpy.typing as npt

from yaml import load
try:
    from yaml import CSafeLoader as Loader
except ImportError: # pragma: no cover
    from yaml import SafeLoader as Loader # type: ignore

from .edges import Edges
from .faces import Faces, _FMFaces, _StructuredFaces
from ..cases import CaseStudy
from ..types import Num, StrOrPath
from .._docs import docstringtemplate
from .._paths import _BaseModelFinder, find_path, get_model

__all__ = ["Edges",
           "Faces",
           "Transect",
           "get_reset_origin",
           "get_normalised_dims",
           "get_normalised_data",
           "get_normalised_data_deficit"]


class Result:
    """Class for capturing the results of executed case studies. Contains
    metadata from the simulation. Automatically detects if the model uses a 
    flexible or structured mesh and then populates edge and face data in the 
    :attr:`edges` and :attr:`faces` attributes, where appropriate.
    
    >>> data_dir = getfixture('data_dir')
    >>> result = Result(data_dir)
    >>> result.x_lim
    (0.0, 18.0)
    
    >>> result.edges.extract_k(-1, 1) #doctest: +ELLIPSIS
                                            geometry            u1   n0   n1
    0      LINESTRING (1.00000 2.00000, 0.00000 2.00000) -3.662849e-17  0.0  1.0
    ...
    
    :param project_path: path to the Delft3D project directory
    
    """
    
    def __init__(self, project_path: StrOrPath):
        
        model_result = get_model(project_path,
                                 _FMModelResults,
                                 _StructuredModelResults)
        
        if model_result is None:
            msg = "No valid model result files detected"
            raise FileNotFoundError(msg)
        
        self._model_result = model_result
    
    @property
    def path(self) -> Path:
        """Path to the Delft3D project directory
        """
        result = self._model_result.project_path
        return Path(result)
    
    @property
    def x_lim(self) -> Tuple[float, float]:
        """Domain limits in the x-direction, in metres
        
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> result.x_lim
        (0.0, 18.0)
        
        """
        result = self._model_result.x_lim
        assert result is not None
        return result
    
    @property
    def y_lim(self) -> Tuple[float, float]:
        """Domain limits in the y-direction, in metres
        
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> result.y_lim
        (1.0, 5.0)
        
        """
        result = self._model_result.y_lim
        assert result is not None
        return result
    
    @property
    def times(self) -> npt.NDArray[np.datetime64]:
        """Time steps of the Delft3D simulation
        
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> result.times
        array(['2001-01-01T00:00:00.000000000', '2001-01-01T01:00:00.000000000'],
        dtype='datetime64[ns]')
        
        """
        result = self._model_result.times
        assert result is not None
        return result
    
    @property
    def edges(self) -> Optional[Edges]:
        """Results on the grid edges for flexible mesh (``'fm'``) models . See 
        the :class:`.Edges` documentation for usage.
        """
        result = self._model_result.edges
        assert result is not None
        return result
    
    @property
    def faces(self) -> Faces:
        """Results on the grid faces. See the :class:`.Faces` documentation
        for usage.
        """
        result = self._model_result.faces
        assert result is not None
        return result
    
    def __repr__(self):
        return f"Result(path={repr(self.path)})"


class _BaseModelResults(_BaseModelFinder):
    
    @property
    @abstractmethod
    def x_lim(self) -> Optional[Tuple[float, float]]:
        pass    # pragma: no cover
    
    @property
    @abstractmethod
    def y_lim(self) -> Optional[Tuple[float, float]]:
        pass    # pragma: no cover
    
    @property
    @abstractmethod
    def times(self) -> Optional[npt.NDArray[np.datetime64]]:
        pass    # pragma: no cover
    
    @property
    @abstractmethod
    def edges(self) -> Optional[Edges]:
        pass    # pragma: no cover
    
    @property
    @abstractmethod
    def faces(self) -> Optional[Faces]:
        pass    # pragma: no cover


class _FMModelResults(_BaseModelResults):
    
    @property
    def path(self) -> Optional[Path]:
        return find_path(self.project_path, ".nc", "_map")
    
    @property
    def x_lim(self) -> Optional[Tuple[float, float]]:
        
        if self.path is None: return None
        
        with xr.open_dataset(self.path) as ds:
            x = ds.mesh2d_node_x.values
        
        return (x.min(), x.max())
    
    @property
    def y_lim(self) -> Optional[Tuple[float, float]]:
        
        if self.path is None: return None
        
        with xr.open_dataset(self.path) as ds:
            y = ds.mesh2d_node_y.values
        
        return (y.min(), y.max())
    
    @property
    def times(self) -> Optional[npt.NDArray[np.datetime64]]:
        
        if self.path is None: return None
        
        with xr.open_dataset(self.path) as ds:
            time = ds.time.values
        
        return time
    
    @property
    def edges(self) -> Optional[Edges]:
        if self.path is None: return None
        assert self.times is not None
        return Edges(self.path, len(self.times))
    
    @property
    def faces(self) -> Optional[Faces]:
        if self.path is None: return None
        assert self.times is not None
        assert self.x_lim is not None
        return _FMFaces(self.path,
                        len(self.times),
                        self.x_lim[1])


class _StructuredModelResults(_BaseModelResults):
    
    @property
    def path(self) -> Optional[Path]:
        return find_path(self.project_path, ".nc", "trim-")
    
    @property
    def x_lim(self) -> Optional[Tuple[float, float]]:
        
        if self.path is None: return None
        
        with xr.open_dataset(self.path) as ds:
            x = ds.XCOR.values
        
        x = x[:-1, :-1]
        
        return (x.min(), x.max())
    
    @property
    def y_lim(self) -> Optional[Tuple[float, float]]:
        
        if self.path is None: return None
        
        with xr.open_dataset(self.path) as ds:
            y = ds.YCOR.values
        
        y = y[:-1, :-1]
        
        return (y.min(), y.max())
    
    @property
    def times(self) -> Optional[npt.NDArray[np.datetime64]]:
        
        if self.path is None: return None
        
        with xr.open_dataset(self.path) as ds:
            time = ds.time.values
        
        return time
    
    @property
    def edges(self) -> Optional[Edges]:
        return None
    
    @property
    def faces(self) -> Optional[Faces]:
        if self.path is None: return None
        assert self.times is not None
        assert self.x_lim is not None
        return _StructuredFaces(self.path,
                                len(self.times),
                                self.x_lim[1])


@dataclass(frozen=True, repr=False)
class Validate():
    """Store for :class:`.Transect` objects
    
    Print the object to see the descriptions and indices of the stored
    :class:`.Transect` objects.
    
    >>> validate = Validate()
    >>> print(validate)
    Validate(0: Centreline velocity
             1: Axial velocity at $x^*=5$)
    
    >>> validate[0].to_xarray() #doctest: +ELLIPSIS
    <xarray.DataArray '$u_0$' (dim_0: 10)>
    array([0.40064647, 0.40064647, 0.39288889, 0.38189899, 0.39806061,
           0.44460606, 0.49309091, 0.54610101, 0.56614141, 0.60622222])
    Coordinates:
        $z$      ... 0
        $x$      (dim_0) float64 0.84 1.4 2.1 2.8 3.5 4.2 4.9 5.6 6.3 7.0
        $y$      (dim_0) float64 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
    ...
    
    Use a :class:`.CaseStudy` object to translate the origin of the transects
    to the turbine position.
    
    >>> from snl_d3d_cec_verify import MycekStudy
    >>> case = MycekStudy()
    >>> validate = Validate(case)
    >>> validate[0].to_xarray() #doctest: +ELLIPSIS
    <xarray.DataArray '$u_0$' (dim_0: 10)>
    array([0.40064647, 0.40064647, 0.39288889, 0.38189899, 0.39806061,
           0.44460606, 0.49309091, 0.54610101, 0.56614141, 0.60622222])
    Coordinates:
        $z$      ... -1
        $x$      (dim_0) float64 6.84 7.4 8.1 8.8 9.5 10.2 10.9 11.6 12.3 13.0
        $y$      (dim_0) float64 3.0 3.0 3.0 3.0 3.0 3.0 3.0 3.0 3.0 3.0
    ...
    
    :param case: Case study from which to get turbine position
    :param data_dir: path to folder containing YAML files representing 
        transects. Each file must have the ``attrs.description`` key set.
        Defaults to ``Path("./mycek2014")``
    
    :raises FileNotFoundError: if ``data_dir`` is not a directory
    
    """
    
    _transects: List[Transect] = field(default_factory=list, init=False)
    case: InitVar[Optional[CaseStudy]] = None #: :meta private:
    data_dir: InitVar[Optional[StrOrPath]] = None #: :meta private:
    
    def __post_init__(self, case: Optional[CaseStudy],
                            data_dir: Optional[StrOrPath]):
        
        if data_dir is None:
            data_dir = _mycek_data_path()
        else:
            data_dir = Path(data_dir)
        
        if not data_dir.is_dir():
            raise FileNotFoundError("Given data_dir is not a directory")
        
        turb_pos_x: Num = 0
        turb_pos_y: Num = 0
        turb_pos_z: Num = 0
        
        if case is not None:
            assert not isinstance(case.turb_pos_x, Sequence)
            assert not isinstance(case.turb_pos_y, Sequence)
            assert not isinstance(case.turb_pos_z, Sequence)
            turb_pos_x = case.turb_pos_x
            turb_pos_y = case.turb_pos_y
            turb_pos_z = case.turb_pos_z
        
        translation = (turb_pos_x, turb_pos_y, turb_pos_z)
        transects = []
        
        for item in sorted(data_dir.iterdir()):
            
            if not item.is_file(): continue
            if not item.suffix == '.yaml': continue
            
            transect = Transect.from_yaml(item, translation)
            transects.append(transect)
        
        object.__setattr__(self, '_transects', transects)
    
    def __getitem__(self, item: int) -> Transect:
        return self._transects[item]
    
    def __len__(self) -> int:
        return len(self._transects)
    
    def __repr__(self):
        
        msg = "Validate("
        indent = len(msg)
        
        if self._transects:
            
            transect = self._transects[0]
            msg += f"0: {transect.attrs['description']}"
            
            for i, transect in enumerate(self._transects[1:]):
                msg += "\n" + " " * indent
                msg += f"{i + 1}: {transect.attrs['description']}"
        
        msg += ")"
        
        return msg


def _mycek_data_path() -> Path:
    this_dir = os.path.dirname(os.path.realpath(__file__))
    return Path(this_dir) / "mycek2014"


# Types definitions
T = TypeVar('T', bound='Transect')
Vector = Tuple[Num, Num, Num]


@docstringtemplate
@dataclass(eq=False, frozen=True)
class Transect():
    """Store for data associated with a transect across the domain, at a 
    particular z-level.
    
    Data is stored for each x and y pair, in order. For example:
    
    >>> x = Transect(-1, [1, 2, 3, 4], [2, 2, 2, 2], [5, 4, 3, 2])
    >>> x.to_xarray() #doctest: +ELLIPSIS
    <xarray.DataArray (dim_0: 4)>
    array([5, 4, 3, 2])
    Coordinates:
        $z$      ... -1
        $x$      (dim_0) ... 1 2 3 4
        $y$      (dim_0) ... 2 2 2 2
    Dimensions without coordinates: dim_0
    
    :class:`.Transect` objects can also be unpacked, like a dictionary, to 
    extract matching data from the :meth:`.Faces.extract_z` method:
    
    >>> from snl_d3d_cec_verify import Result
    >>> data_dir = getfixture('data_dir')
    >>> result = Result(data_dir)
    >>> result.faces.extract_z(-1, **x) #doctest: +ELLIPSIS
    <xarray.Dataset>
    Dimensions:  (dim_0: 4)
    Coordinates:
        $z$      ... -1
        time     datetime64[ns] 2001-01-01T01:00:00
        $x$      (dim_0) ... 1 2 3 4
        $y$      (dim_0) ... 2 2 2 2
    Dimensions without coordinates: dim_0
    Data variables:
        k        (dim_0) float64 1.002 1.002 1.002 1.001
        $u$      (dim_0) float64 0.7793 0.7776 0.7766 0.7757
        $v$      (dim_0) float64 1.193e-17 4.679e-17 2.729e-17 -2.519e-17
        $w$      (dim_0) float64 -0.001658 0.0001347 -0.00114 0.0002256
    
    :param z: z-level of the transect, in meters
    :param x: x-coordinates of the transect, in meters
    :param y: y-coordinates of the transect, in meters
    :param data: values at each point along the transect
    :param name: name of the data stored in the transect
    :param attrs: meta data associated with the transect
    :param translation: translation of the transect origin, defaults to
        {translation}
    
    :raises ValueError: if the lengths of ``x``, ``y``, or ``data`` do not
        match
    
    """
    
    #: z-level of the transect, in meters
    z: Num = field(repr=False) 
    
    #: x-coordinates of the transect, in meters
    x: npt.NDArray[np.float64] = field(repr=False)
    
    #: y-coordinates of the transect, in meters
    y: npt.NDArray[np.float64] = field(repr=False)
    
    #: values at each point along the transect
    data: Optional[npt.NDArray[np.float64]] = field(default=None, repr=False)
    
    #: name of the data stored in the transect
    name: Optional[str] = None
    
    #: meta data associated with the transect
    attrs: Optional[dict[str, str]] = None
    
    translation: InitVar[Vector] = (0, 0, 0) #: :meta private:
    
    def __post_init__(self, translation: Vector):
        
        if len(self.x) != len(self.y):
            raise ValueError("Length of x and y must match")
        
        if self.data is not None and len(self.data) != len(self.x):
            raise ValueError("Length of data must match x and y")
        
        z = self.z + translation[2]
        x = np.array(self.x) + translation[0]
        y = np.array(self.y) + translation[1]
        
        # Overcome limitation of frozen flag
        object.__setattr__(self, 'z', z)
        object.__setattr__(self, 'x', x)
        object.__setattr__(self, 'y', y)
        
        if self.data is None: return
        
        data = np.array(self.data)
        object.__setattr__(self, 'data', data)
    
    @docstringtemplate
    @classmethod
    def from_csv(cls: Type[T], path: StrOrPath,
                               name: Optional[str] = None,
                               attrs: Optional[dict[str, str]] = None,
                               translation: Vector = (0, 0, 0)) -> T:
        """Create a new :class:`.Transect` object from a CSV file. 
        
        The CSV file must have ``x``, ``y``, and ``z`` column headers, and
        optionally a ``data`` column header. For example::
            
            x, y, z, data
            7, 3, 0, 1
            8, 3, 0, 2
            9, 3, 0, 3
        
        :param path: path to the CSV file to load
        :param name: name of data in the resulting :class:`.Transect` object
        :param attrs: attributes for the resulting :class:`.Transect` object
        :param translation: translation of the transect origin, defaults to
            {translation}
        
        :raises ValueError: if the unique values in the z-column is greater
            than one
        
        :rtype: Transect
        
        """
        
        path = Path(path).resolve(strict=True)
        cols = defaultdict(list)
        keys = ["x", "y", "z", "data"]
        
        with open(path) as csvfile:
            
            reader = csv.DictReader(csvfile)
            
            for row, key in itertools.product(reader, keys):
                if key in row: cols[key].append(float(row[key]))
        
        z = list(set(cols["z"]))
        data = np.array(cols.pop("data")) if "data" in cols else None
        
        if len(z) != 1:
            raise ValueError("Transect only supports fixed z-value")
        
        if attrs is None: attrs = {}
        attrs["path"] = str(path)
        
        return cls(z[0],
                   np.array(cols["x"]),
                   np.array(cols["y"]),
                   data=data,
                   name=name,
                   attrs=attrs,
                   translation=translation)
    
    @docstringtemplate
    @classmethod
    def from_yaml(cls: Type[T], path: StrOrPath,
                                translation: Vector = (0, 0, 0)) -> T:
        """Create a new :class:`.Transect` object from a YAML file. 
        
        The YAML file must have ``z`` , ``x`` and ``y``, and keys where ``z``
        is a single value and ``x`` and ``y`` are arrays.
        
        Optionally, a ``data`` key can be given as an array, ``name`` key as a
        single value (treated as a string) and an ``attrs`` key with a nested
        dictionary. For example::
            
            z: -1.0
            x: [7, 8, 9]
            y: [3, 3, 3]
            data: [1, 2, 3]
            name: $\\gamma_0$
            attrs:
                mock: mock
                path: not mock
        
        :param path: path to the YAML file to load
        :param translation: translation of the transect origin, defaults to
            {translation}
        
        :rtype: Transect
        
        """
        
        path = Path(path).resolve(strict=True)
        
        with open(path) as yamlfile:
            raw = load(yamlfile, Loader=Loader)
        
        data = None
        name = None
        attrs = {}
        
        if "data" in raw: data = np.array(raw["data"])
        if "name" in raw: name = raw["name"]
        if "attrs" in raw: attrs = raw["attrs"]
        attrs["path"] = str(path)
        
        return cls(raw["z"],
                   x=np.array(raw["x"]),
                   y=np.array(raw["y"]),
                   data=data,
                   name=name,
                   attrs=attrs,
                   translation=translation)
    
    def keys(self):
        """
        :meta private:
        """
        return KeysView(["kz", "x", "y"])
    
    def to_xarray(self) -> xr.DataArray:
        """Export transect as a :class:`xarray.DataArray` object.
        
        :rtype: xarray.DataArray
        
        """
        
        keys = [f"${x}$" for x in ["z", "x", "y"]]
        coords: Mapping[Hashable, Any] = {keys[0]: self.z,
                                          keys[1]: ("dim_0", self.x),
                                          keys[2]: ("dim_0", self.y)}
        
        if self.data is None:
            return xr.DataArray([np.nan] * len(self.x),
                                coords=coords,
                                name=self.name)
        
        return xr.DataArray(self.data,
                            coords=coords,
                            name=self.name,
                            attrs=self.attrs)
    
    def __eq__(self, other: Any) -> bool:
        
        if not isinstance(other, Transect):
            return NotImplemented
        
        if not self.z == other.z: return False
        if not np.isclose(self.x, other.x).all(): return False
        if not np.isclose(self.y, other.y).all(): return False
        
        none_check = sum([1 if x is None else 0 for x in
                                                  [self.data, other.data]])
        
        if none_check == 1: return False
        
        if none_check == 0:
            assert self.data is not None
            assert other.data is not None
            if not np.isclose(self.data, other.data).all(): return False
        
        optionals = ("name", "attrs")
        
        for key in optionals:
            
            none_check = sum([1 if x is None else 0 for x in (self[key],
                                                              other[key])])
            
            if none_check == 1: return False
            if none_check == 0 and self[key] != other[key]: return False
        
        return True
    
    def __getitem__(self, item: str) -> Union[None,
                                              Num,
                                              npt.NDArray[np.float64]]:
        if item == "kz": item = "z"
        return getattr(self, item)


def get_reset_origin(da: xr.DataArray,
                     origin: Vector) -> xr.DataArray:
    """Move the origin in the given :class:`xarray.DataArray` object to the
    given location
    
    The given :class:`xarray.DataArray` object must have coordinates
    containing the characters ``x``, ``y`` and ``z``.
    
    :param da: object to modify.
    :type da: xarray.DataArray
    :param origin: updated origin
    
    :rtype: xarray.DataArray
    
    """
    
    axes_coords = _get_axes_coords(list(da.coords.keys()))
    axes_new = [da[coord].values - val
                                for coord, val in zip(axes_coords, origin)]
    
    new_da = da.assign_coords({axes_coords[2]: axes_new[2],
                               axes_coords[0]: ("dim_0", axes_new[0]),
                               axes_coords[1]: ("dim_0", axes_new[1])})
    
    return new_da


def get_normalised_dims(da: xr.DataArray, factor: Num) -> xr.DataArray:
    """Normalise the coordinates in the given :class:`xarray.DataArray` object
    by the given factor.
    
    The given :class:`xarray.DataArray` object must have coordinates
    containing the characters ``x``, ``y`` and ``z``. The returned object will
    replace these coordinated with starred versions.
    
    :param da: object to modify
    :type da: xarray.DataArray
    :param factor: normalising factor, coordinates are divided by this value
    
    :rtype: xarray.DataArray
    
    """
    
    axes_coords = _get_axes_coords(list(da.coords.keys()))
    axes_star = [da[coord].values / factor for coord in axes_coords]
    
    new_da = da.assign_coords({axes_coords[2]: axes_star[2],
                               axes_coords[0]: ("dim_0", axes_star[0]),
                               axes_coords[1]: ("dim_0", axes_star[1])})
    
    star_coord_names = {}
    
    for coord in axes_coords:
        star_coord_names[coord] = _add_star(coord)
    
    new_da = new_da.rename(star_coord_names)
    
    return new_da


def get_normalised_data(da: xr.DataArray, factor: Num) -> xr.DataArray:
    """Normalise the data in the given :class:`xarray.DataArray` object
    by the given factor
    
    If the given :class:`xarray.DataArray` object is named, the name will be
    replaced with a starred version.
    
    :param da: object to modify.
    :type da: xarray.DataArray
    :param factor: normalising factor, the data is divided by this value
    
    :rtype: xarray.DataArray
    
    """
    datastar = da.values / factor
    name = str(da.name)
    
    if name is not None:
        name = _add_star(name)
    
    return xr.DataArray(datastar,
                        coords=da.coords,
                        name=name,
                        attrs=da.attrs)


def get_normalised_data_deficit(da: xr.DataArray,
                                factor: Num,
                                name: Optional[str] = None) -> xr.DataArray:
    """Normalise the data in the given :class:`xarray.DataArray` object
    by the given factor as a percentage deficit of that factor
    
    if :math:`x` is the data and :math:`f` is the normalising factor, then
    the quantity generated by this function is:
    
    .. math::
        
       100 * (1 - x / f)
    
    :param da: object to modify
    :type da: xarray.DataArray
    :param factor: normalising factor, the data is divided by this value
    :param name: name for the resulting data
    
    :rtype: xarray.DataArray
    
    """
    
    data = 100 * (1 - da.values / factor)
    
    return xr.DataArray(data,
                        coords=da.coords,
                        name=name,
                        attrs=da.attrs)


def _get_axes_coords(coords: List[str]) -> Tuple[str, str, str]:
    
    axes = ["x", "y", "z"]
    axes_coords = []
    
    for ax in axes:
        axes_coord = None
        for coord in coords: 
            if ax in coord: axes_coord = coord
        if axes_coord is None:
            raise KeyError(f"Axis {ax} not found")
        axes_coords.append(axes_coord)
    
    t: Tuple[str, str, str] = (axes_coords[0],
                               axes_coords[1],
                               axes_coords[2])
    
    return t


def _add_star(name: str) -> str:
    
    name_dollars = name.count("$")
    
    if name_dollars > 0 and (name_dollars % 2) == 0:
        last_dollar = name.rfind("$")
        name = name[:last_dollar] + "^*" + name[last_dollar:]
    else:
        name = name + " *"
    
    return name
