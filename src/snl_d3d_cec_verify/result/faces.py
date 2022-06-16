# -*- coding: utf-8 -*-

from __future__ import annotations

import itertools
import collections
from abc import ABC, abstractmethod
from typing import (cast,
                    Any,
                    Callable,
                    Dict,
                    List,
                    Optional,
                    Sequence,
                    TypeVar,
                    Union,
                    TYPE_CHECKING)
from functools import wraps
from dataclasses import dataclass, field

import numpy as np
import pandas as pd # type: ignore
import xarray as xr
from scipy import interpolate # type: ignore

from .base import _TimeStepResolver
from .edges import _map_to_edges_geoframe
from ..cases import CaseStudy
from ..types import Num, StrOrPath
from .._docs import docstringtemplate

if TYPE_CHECKING: # pragma: no cover
    import numpy.typing as npt

# Generic for decorators
F = TypeVar('F', bound=Callable[..., Any])


def _extract(func: F) -> F:
    
    @wraps(func)
    def wrapper(self, t_step: int,
                      value: Num,
                      x: Optional[Sequence[Num]] = None,
                      y: Optional[Sequence[Num]] = None) -> xr.Dataset:
        
        do_interp = sum((bool(x is not None),
                         bool(y is not None)))
        
        if do_interp == 1:
            raise RuntimeError("x and y must both be set")
        
        t_step = self._resolve_t_step(t_step)
        
        if t_step not in self._t_steps:
            self._load_t_step(t_step)
        
        ds = func(self, t_step, value, x, y)
        
        if not do_interp: return ds
        
        return ds.interp({"$x$": xr.DataArray(x),
                          "$y$": xr.DataArray(y)})
        
    return cast(F, wrapper)


@dataclass
class _FacesDataClassMixin(_TimeStepResolver):
    xmax: Num #: maximum range in x-direction, in metres
    _t_steps: Dict[int, pd.Timestamp] = field(default_factory=dict,
                                              init=False,
                                              repr=False)
    _frame: Optional[pd.DataFrame] = field(default=None,
                                           init=False,
                                           repr=False)


class Faces(ABC, _FacesDataClassMixin):
    """Class for extracting results on the faces of the simulation grid. Use in
    conjunction with the :class:`.Result` class.
    
    >>> from snl_d3d_cec_verify import Result
    >>> data_dir = getfixture('data_dir')
    >>> result = Result(data_dir)
    >>> result.faces.extract_z(-1, -1) #doctest: +ELLIPSIS
    <xarray.Dataset>
    Dimensions:   ($x$: 18, $y$: 4)
    Coordinates:
      * $x$       ($x$) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
      * $y$       ($y$) float64 1.5 2.5 3.5 4.5
        $z$       ... -1
        time      datetime64[ns] 2001-01-01T01:00:00
    Data variables:
        $\\sigma$  ($x$, $y$) float64 -0.4994 -0.4994 -0.4994 ... -0.5 -0.5 -0.5
        $u$       ($x$, $y$) float64 0.781 0.781 0.781 ... 0.7763 0.7763 0.7763
        $v$       ($x$, $y$) float64 -3.237e-18 1.423e-17 ... -8.598e-17 -4.824e-17
        $w$       ($x$, $y$) float64 -0.01472 -0.01472 ... 0.001343 0.001343
        $k$       ($x$, $y$) float64 0.004802 0.004765 ... 0.003674 0.0036...
    
    :param nc_path: path to the ``.nc`` file containing results
    :param n_steps: number of time steps in the simulation
    :param xmax: maximum range in x-direction, in metres
    
    """
    
    @docstringtemplate
    def extract_turbine_centre(self, t_step: int,
                                     case: CaseStudy,
                                     offset_x: Num = 0,
                                     offset_y: Num = 0,
                                     offset_z: Num = 0) -> xr.Dataset:
        """Extract data at the turbine centre, as defined in the given
        :class:`.CaseStudy` object. Available data is:
        
        * :code:`sigma`: sigma layer
        * :code:`u`: velocity in the x-direction, in metres per second
        * :code:`v`: velocity in the x-direction, in metres per second
        * :code:`w`: velocity in the x-direction, in metres per second
        * :code:`k`: turbulent kinetic energy, in metres squared per second
          squared
        
        Results are returned as a :class:`xarray.Dataset`. For example:
        
        >>> from snl_d3d_cec_verify import MycekStudy, Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> case = MycekStudy()
        >>> result.faces.extract_turbine_centre(-1, case) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:  (dim_0: 1)
        Coordinates:
            $z$       ... -1
            time      datetime64[ns] 2001-01-01T01:00:00
            $x$       (dim_0) ... 6
            $y$       (dim_0) ... 3
        Dimensions without coordinates: dim_0
        Data variables:
            $\\sigma$  (dim_0) float64 -0.4996
            $u$       (dim_0) float64 0.7748
            $v$       (dim_0) float64 -2.942e-17
            $w$       (dim_0) float64 0.0002786
            $k$       (dim_0) float64 0.004...
        
        The position extracted can also be shifted using the ``offset_x``,
        ``offset_y`` and ``offset_z`` parameters.
        
        :param t_step: Time step index
        :param case: Case study from which to get turbine position
        :param offset_x: Shift x-coordinate of extraction point, in metres.
            Defaults to {offset_x}
        :param offset_y: Shift y-coordinate of extraction point, in metres.
            Defaults to {offset_y}
        :param offset_z: Shift z-coordinate of extraction point, in metres.
            Defaults to {offset_z}
        
        :raises IndexError: if the time-step index (``t_step``) is out of
            range
        :raises ValueError: if the length of the :class:`.CaseStudy` object is
            greater than one
        
        :rtype: xarray.Dataset
        
        """
        
        _check_case_study(case)
        
        # Inform the type checker that we have Num for single value cases
        turb_pos_z = cast(Num, case.turb_pos_z)
        turb_pos_x = cast(Num, case.turb_pos_x)
        turb_pos_y = cast(Num, case.turb_pos_y)
        
        return self.extract_z(t_step,
                              turb_pos_z + offset_z,
                              [turb_pos_x + offset_x],
                              [turb_pos_y + offset_y])
    
    @docstringtemplate
    def extract_turbine_centreline(self, t_step: int,
                                         case: CaseStudy,
                                         x_step: Num = 0.5,
                                         offset_x: Num = 0,
                                         offset_y: Num = 0,
                                         offset_z: Num = 0) -> xr.Dataset:
        """Extract data along the turbine centreline, from the turbine
        position defined in the given :class:`.CaseStudy` object. Available 
        data is:
        
        * :code:`k`: sigma layer
        * :code:`u`: velocity in the x-direction, in metres per second
        * :code:`v`: velocity in the x-direction, in metres per second
        * :code:`w`: velocity in the x-direction, in metres per second
        * :code:`k`: turbulent kinetic energy, in metres squared per second
          squared
        
        Results are returned as a :class:`xarray.Dataset`. Use the ``x_step``
        argument to control the frequency of samples. For example:
        
        >>> from snl_d3d_cec_verify import MycekStudy, Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> case = MycekStudy()
        >>> result.faces.extract_turbine_centreline(-1, case, x_step=1) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:   (dim_0: 13)
        Coordinates:
            $z$       ... -1
            time      datetime64[ns] 2001-01-01T01:00:00
            $x$       (dim_0) float64 6.0 7.0 8.0 9.0 10.0 ... 14.0 15.0 16.0 17.0 18.0
            $y$       (dim_0) ... 3 3 3 3 3 3 3 3 3 3 3 3 3
        Dimensions without coordinates: dim_0
        Data variables:
            $\\sigma$  (dim_0) float64 -0.4996 -0.4996 -0.4996 ... -0.4999 -0.4999 nan
            $u$       (dim_0) float64 0.7748 0.7747 0.7745 0.7745 ... 0.7759 0.7762 nan
            $v$       (dim_0) float64 -2.942e-17 4.192e-17 9.126e-17 ... -8.523e-17 nan
            $w$       (dim_0) float64 0.0002786 -0.0004764 0.0003097 ... -7.294e-05 nan
            $k$       (dim_0) float64 0.004307 0.004229 0.004157 ... 0.003691 nan
        
        The position extracted can also be shifted using the ``offset_x``,
        ``offset_y`` and ``offset_z`` parameters.
        
        :param t_step: Time step index
        :param case: Case study from which to get turbine position
        :param x_step: Sample step, in metres. Defaults to {x_step}
        :param offset_x: Shift x-coordinate of extraction point, in metres.
            Defaults to {offset_x}
        :param offset_y: Shift y-coordinate of extraction point, in metres.
            Defaults to {offset_y}
        :param offset_z: Shift z-coordinate of extraction point, in metres.
            Defaults to {offset_z}
        
        :raises IndexError: if the time-step index (``t_step``) is out of
            range
        :raises ValueError: if the length of the :class:`.CaseStudy` object is
            greater than one
        
        :rtype: xarray.Dataset
        
        """
        
        _check_case_study(case)
        
        # Inform the type checker that we have Num for single value cases
        turb_pos_z = cast(Num, case.turb_pos_z)
        turb_pos_x = cast(Num, case.turb_pos_x)
        turb_pos_y = cast(Num, case.turb_pos_y)
        
        x = np.arange(turb_pos_x + offset_x, self.xmax, x_step)
        if np.isclose(x[-1] + x_step, self.xmax): x = np.append(x, self.xmax)
        y = [turb_pos_y + offset_y] * len(x)
        
        return self.extract_z(t_step, turb_pos_z + offset_z, list(x), y)
    
    def extract_turbine_z(self, t_step: int,
                                case: CaseStudy,
                                offset_z: Num = 0) -> xr.Dataset:
        """Extract data from the z-plane interseting the turbine centre, as
        defined in the given :class:`.CaseStudy` object, at the face centres.
        Available data is:
        
        * :code:`k`: sigma layer
        * :code:`u`: velocity in the x-direction, in metres per second
        * :code:`v`: velocity in the x-direction, in metres per second
        * :code:`w`: velocity in the x-direction, in metres per second
        * :code:`k`: turbulent kinetic energy, in metres squared per second
          squared
        
        Results are returned as a :class:`xarray.Dataset`.For example:
        
        >>> from snl_d3d_cec_verify import MycekStudy, Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> case = MycekStudy()
        >>> result.faces.extract_turbine_z(-1, case) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:   ($x$: 18, $y$: 4)
        Coordinates:
          * $x$       ($x$) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
          * $y$       ($y$) float64 1.5 2.5 3.5 4.5
            $z$       ... -1
            time      datetime64[ns] 2001-01-01T01:00:00
        Data variables:
            $\\sigma$  ($x$, $y$) float64 -0.4994 -0.4994 -0.4994 ... -0.5 -0.5 -0.5
            $u$       ($x$, $y$) float64 0.781 0.781 0.781 ... 0.7763 0.7763 0.7763
            $v$       ($x$, $y$) float64 -3.237e-18 1.423e-17 ... -8.598e-17 -4.824e-17
            $w$       ($x$, $y$) float64 -0.01472 -0.01472 ... 0.001343 0.001343
            $k$       ($x$, $y$) float64 0.004802 0.004765 ... 0.003674 0.0036...
        
        The z-plane can be shifted using the ``offset_z`` parameter.
        
        :param t_step: Time step index
        :param case: Case study from which to get turbine position
        :param offset_z: Shift z-coordinate of extraction point, in metres.
            Defaults to {offset_z}
        
        :raises IndexError: if the time-step index (``t_step``) is out of
            range
        :raises ValueError: if the length of the :class:`.CaseStudy` object is
            greater than one
        
        :rtype: xarray.Dataset
        
        """
        
        _check_case_study(case)
        turb_pos_z = cast(Num, case.turb_pos_z)
        
        return self.extract_z(t_step, turb_pos_z + offset_z)
    
    @_extract
    def extract_z(self, t_step: int,
                        z: Num,
                        x: Optional[Sequence[Num]] = None,
                        y: Optional[Sequence[Num]] = None) -> xr.Dataset:
        """Extract data on the plane at the given z-level. Available data is:
        
        * :code:`sigma`: sigma value
        * :code:`u`: velocity in the x-direction, in metres per second
        * :code:`v`: velocity in the x-direction, in metres per second
        * :code:`w`: velocity in the x-direction, in metres per second
        * :code:`k`: turbulent kinetic energy, in metres squared per second
          squared
        
        Results are returned as a :class:`xarray.Dataset`. If the ``x`` and 
        ``y`` parameters are defined, then the results are interpolated onto
        the given coordinates. For example:
        
        >>> from snl_d3d_cec_verify import Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> x = [6, 7, 8, 9, 10]
        >>> y = [2, 2, 2, 2, 2]
        >>> result.faces.extract_z(-1, -1, x, y) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:   (dim_0: 5)
        Coordinates:
            $z$       ... -1
            time      datetime64[ns] 2001-01-01T01:00:00
            $x$       (dim_0) ... 6 7 8 9 10
            $y$       (dim_0) ... 2 2 2 2 2
        Dimensions without coordinates: dim_0
        Data variables:
            $\\sigma$  (dim_0) float64 -0.4996 -0.4996 -0.4996 -0.4997 -0.4997
            $u$       (dim_0) float64 0.7748 0.7747 0.7745 0.7745 0.7746
            $v$       (dim_0) float64 -3.877e-18 4.267e-17 5.452e-17 5.001e-17 8.011e-17
            $w$       (dim_0) float64 0.0002786 -0.0004764 ... -0.0002754 0.0003252
            $k$       (dim_0) float64 0.004317 0.0042... 0.00416... 0.00409... 0.00403...
        
        If ``x`` and ``y`` are not given, then the results are returned at the
        face centres.
        
        >>> result.faces.extract_z(-1, -1) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:   ($x$: 18, $y$: 4)
        Coordinates:
          * $x$       ($x$) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
          * $y$       ($y$) float64 1.5 2.5 3.5 4.5
            $z$       ... -1
            time      datetime64[ns] 2001-01-01T01:00:00
        Data variables:
            $\\sigma$  ($x$, $y$) float64 -0.4994 -0.4994 -0.4994 ... -0.5 -0.5 -0.5
            $u$       ($x$, $y$) float64 0.781 0.781 0.781 ... 0.7763 0.7763 0.7763
            $v$       ($x$, $y$) float64 -3.237e-18 1.423e-17 ... -8.598e-17 -4.824e-17
            $w$       ($x$, $y$) float64 -0.01472 -0.01472 ... 0.001343 0.001343
            $k$       ($x$, $y$) float64 0.004802 0.004765 ... 0.003674 0.0036...
        
        :param t_step: Time step index
        :param z: z-level at which to extract data
        :param x: x-coordinates on which to interpolate data
        :param y: y-coordinates on which to interpolate data
        
        :raises IndexError: if the time-step index (``t_step``) is out of
            range
        :raises RuntimeError: if only ``x`` or ``y`` is set
        
        :rtype: xarray.Dataset
        
        """
        
        return _faces_frame_to_slice(self._frame,
                                     self._t_steps[t_step],
                                     "z",
                                     z)
    
    @_extract
    def extract_sigma(self, t_step: int,
                            sigma: float,
                            x: Optional[Sequence[Num]] = None,
                            y: Optional[Sequence[Num]] = None) -> xr.Dataset:
        """Extract data on the plane at the given sigma-level. Available
        data is:
        
        * :code:`z`: the z-level, in metres
        * :code:`u`: velocity in the x-direction, in metres per second
        * :code:`v`: velocity in the x-direction, in metres per second
        * :code:`w`: velocity in the x-direction, in metres per second
        * :code:`k`: turbulent kinetic energy, in metres squared per second
          squared
        
        Results are returned as a :class:`xarray.Dataset`. If the ``x`` and 
        ``y`` parameters are defined, then the results are interpolated onto
        the given coordinates. For example:
        
        >>> from snl_d3d_cec_verify import Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> x = [6, 7, 8, 9, 10]
        >>> y = [2, 2, 2, 2, 2]
        >>> result.faces.extract_sigma(-1, -0.5, x, y) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:   (dim_0: 5)
        Coordinates:
            $\\sigma$  ... -0.5
            time      datetime64[ns] 2001-01-01T01:00:00
            $x$       (dim_0) ... 6 7 8 9 10
            $y$       (dim_0) ... 2 2 2 2 2
        Dimensions without coordinates: dim_0
        Data variables:
            $z$       (dim_0) float64 -1.001 -1.001 -1.001 -1.001 -1.001
            $u$       (dim_0) float64 0.7747 0.7746 0.7744 0.7745 0.7745
            $v$       (dim_0) float64 -3.88e-18 4.267e-17 5.452e-17 5.002e-17 8.013e-17
            $w$       (dim_0) float64 0.0002791 -0.0004769 ... -0.0002756 0.0003256
            $k$       (dim_0) float64 0.004... 0.0042... 0.0041... 0.004... 0.0040...
        
        If ``x`` and ``y`` are not given, then the results are returned at the
        face centres.
        
        >>> result.faces.extract_sigma(-1, -0.5) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:   ($x$: 18, $y$: 4)
        Coordinates:
          * $x$       ($x$) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
          * $y$       ($y$) float64 1.5 2.5 3.5 4.5
            $\\sigma$  ... -0.5
            time      datetime64[ns] 2001-01-01T01:00:00
        Data variables:
            $z$       ($x$, $y$) float64 -1.001 -1.001 -1.001 -1.001 ... -1.0 -1.0 -1.0
            $u$       ($x$, $y$) float64 0.7809 0.7809 0.7809 ... 0.7763 0.7763 0.7763
            $v$       ($x$, $y$) float64 -3.29e-18 1.419e-17 ... -8.598e-17 -4.824e-17
            $w$       ($x$, $y$) float64 -0.01473 -0.01473 ... 0.001343 0.001343
            $k$       ($x$, $y$) float64 0.004809 0.004772 ... 0.003674 0.0036...
        
        :param t_step: Time step index
        :param sigma: sigma-level at which to extract data
        :param x: x-coordinates on which to interpolate data
        :param y: y-coordinates on which to interpolate data
        
        :raises IndexError: if the time-step index (``t_step``) is out of
            range
        :raises RuntimeError: if only ``x`` or ``y`` is set
        
        :rtype: xarray.Dataset
        
        """
        
        return _faces_frame_to_slice(self._frame,
                                     self._t_steps[t_step],
                                     "sigma",
                                     sigma)
    
    def extract_depth(self, t_step: int) -> xr.DataArray:
        """Extract the depth, in meters, at each of the face centres.
        
        Results are returned as a :class:`xarray.DataArray`. For example:
        
        >>> from snl_d3d_cec_verify import Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> result.faces.extract_depth(-1)
        <xarray.DataArray 'depth' ($x$: 18, $y$: 4)>
        array([[2.00234445, 2.00234445, 2.00234445, 2.00234445],
               [2.00224624, 2.00224624, 2.00224624, 2.00224624],
               [2.00212823, 2.00212823, 2.00212823, 2.00212823],
               [2.00201275, 2.00201275, 2.00201275, 2.00201275],
               [2.00188605, 2.00188605, 2.00188605, 2.00188605],
               [2.00176218, 2.00176218, 2.00176218, 2.00176218],
               [2.00163089, 2.00163089, 2.00163089, 2.00163089],
               [2.00150178, 2.00150178, 2.00150178, 2.00150178],
               [2.0013675 , 2.0013675 , 2.0013675 , 2.0013675 ],
               [2.00123502, 2.00123502, 2.00123502, 2.00123502],
               [2.00109849, 2.00109849, 2.00109849, 2.00109849],
               [2.00096352, 2.00096352, 2.00096352, 2.00096352],
               [2.0008259 , 2.0008259 , 2.0008259 , 2.0008259 ],
               [2.00068962, 2.00068962, 2.00068962, 2.00068962],
               [2.0005524 , 2.0005524 , 2.0005524 , 2.0005524 ],
               [2.00041653, 2.00041653, 2.00041653, 2.00041653],
               [2.00027887, 2.00027887, 2.00027887, 2.00027887],
               [2.00014281, 2.00014281, 2.00014281, 2.00014281]])
        Coordinates:
          * $x$      ($x$) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
          * $y$      ($y$) float64 1.5 2.5 3.5 4.5
            time     datetime64[ns] 2001-01-01T01:00:00
        
        :param t_step: Time step index
        
        :raises IndexError: if the time-step index (``t_step``) is out of
            range
        
        :rtype: xarray.DataArray
        
        """
        
        t_step = self._resolve_t_step(t_step)
        
        if t_step not in self._t_steps:
            self._load_t_step(t_step)
        
        return _faces_frame_to_depth(self._frame,
                                     self._t_steps[t_step])
    
    def _load_t_step(self, t_step: int):
        
        t_step = self._resolve_t_step(t_step)
        if t_step in self._t_steps: return
        
        frame = self._get_faces_frame(t_step)
        
        if self._frame is None:
            self._frame = frame
        else:
            self._frame = pd.concat([self._frame, frame],
                                    ignore_index=True)
        
        self._t_steps[t_step] = pd.Timestamp(frame["time"].unique().take(0))
    
    @abstractmethod
    def _get_faces_frame(self, t_step: int) -> pd.DataFrame:
        pass    # pragma: no cover


def _check_case_study(case: CaseStudy):
    if len(case) != 1:
        raise ValueError("case study must have length one")


def _faces_frame_to_slice(frame: pd.DataFrame,
                          sim_time: pd.Timestamp,
                          key: str,
                          value: Num) -> xr.Dataset:
    
    valid_keys = ['z', 'sigma']
    
    if key not in valid_keys:
        keys_msg = ", ".join(valid_keys)
        err_msg = f"Given key is not valid. Choose from {keys_msg}"
        raise RuntimeError(err_msg)
    
    valid_keys.remove(key)
    other_key = valid_keys[0]
    
    frame = frame.set_index(['x', 'y', 'time'])
    frame = frame.xs(sim_time, level=2)
    
    data = collections.defaultdict(list)
    remove_nans = lambda a: a[:, ~np.isnan(a).any(axis=0)]
    
    for (x, y), group in frame.groupby(level=[0, 1]):
        
        cols = ["z", "sigma", "u", "v", "w"]
        if "tke" in group: cols.append("tke")
        
        group = group.reset_index(drop=True)
        group_values = group[cols].to_numpy().T
        
        zsig = group_values[:2, :]
        zsig = remove_nans(zsig)
        
        if key == "z":
            
            get_sigma = interpolate.interp1d(zsig[0, :],
                                             zsig[1, :],
                                             fill_value="extrapolate")
            sigma = float(get_sigma(value))
            other = sigma
        
        else:
            
            get_z = interpolate.interp1d(zsig[1, :],
                                         zsig[0, :],
                                         fill_value="extrapolate")
            other = float(get_z(value))
            sigma = value
        
        sigvel = group_values[1:5, :]
        sigvel = remove_nans(sigvel)
        get_vel = interpolate.interp1d(sigvel[0, :],
                                       sigvel[1:, :],
                                       fill_value="extrapolate")
        vel = get_vel(sigma)
        
        if "tke" in group:
            
            sigtke = group_values[[1, 5], :]
            sigtke = remove_nans(sigtke)
            get_tke = interpolate.interp1d(sigtke[0, :],
                                           sigtke[1:, :],
                                           fill_value="extrapolate")
            tke = get_tke(sigma)
        
        data["x"].append(x)
        data["y"].append(y)
        data[other_key].append(other)
        data["u"].append(vel[0])
        data["v"].append(vel[1])
        data["w"].append(vel[2])
        
        if "tke" in group:
            data["tke"].append(tke[0])
    
    zframe = pd.DataFrame(data)
    zframe = zframe.set_index(['x', 'y'])
    ds = zframe.to_xarray()
    ds = ds.assign_coords({key: value})
    
    ds = ds.assign_coords({"time": sim_time})
    
    name_map = {"z": "$z$",
                "x": "$x$",
                "y": "$y$",
                "u": "$u$",
                "v": "$v$",
                "w": "$w$",
                "sigma": r"$\sigma$"}
    if "tke" in data: name_map["tke"] = "$k$"
    
    ds = ds.rename(name_map)
    
    return ds


def _faces_frame_to_depth(frame: pd.DataFrame,
                          sim_time: pd.Timestamp) -> xr.DataArray:
    
    frame = frame[['x', 'y', 'sigma', 'time', 'depth']]
    frame = frame.dropna()
    sigma = frame["sigma"].unique().take(0)
    frame = frame.set_index(['x', 'y', 'sigma', 'time'])
    frame = frame.xs((sigma, sim_time), level=(2, 3))
    ds = frame.to_xarray()
    ds = ds.assign_coords({"time": sim_time})
    ds = ds.rename({"x": "$x$",
                    "y": "$y$"})
    
    return ds.depth


class _FMFaces(Faces):
    def _get_faces_frame(self, t_step: int) -> pd.DataFrame:
        return  _map_to_faces_frame_with_tke(self.nc_path, t_step)


def _map_to_faces_frame_with_tke(map_path: StrOrPath,
                                 t_step: int = None) -> pd.DataFrame:
    
    faces = _map_to_faces_frame(map_path, t_step)
    edges = _map_to_edges_geoframe(map_path, t_step)
    
    times = faces["time"].unique()
    facesi = faces.set_index("time")
    edgesi = edges.set_index("time")
    
    faces_final = pd.DataFrame()
    
    for time in times:
        
        facest = facesi.loc[time]
        edgest = edgesi.loc[time]
        
        facest = facest.reset_index(drop=True)
        edgest = edgest.reset_index(drop=True)
        
        edgest["x"] = edgest['geometry'].apply(
                    lambda line: np.array(line.centroid.coords[0])[0])
        edgest["y"] = edgest['geometry'].apply(
                    lambda line: np.array(line.centroid.coords[0])[1])
        edgesdf = pd.DataFrame(edgest[["x", 
                                       "y",
                                       "sigma",
                                       "turkin1",
                                       "f0",
                                       "f1"]])
        
        facest = facest.set_index(["x", "y", "sigma"])
        facest = facest.sort_index()
        
        x = facest.index.get_level_values(0).unique().values
        y = facest.index.get_level_values(1).unique().values
        grid_x, grid_y = np.meshgrid(x, y)
        
        facest_new = facest.copy()
        
        for sigma, group in edgesdf.groupby(by="sigma"):
            
            # Fill missing values
            groupna = group[pd.isna(group["turkin1"])]
            group = group[~pd.isna(group["turkin1"])]
            if group.empty: continue
            
            points = np.array(list(zip(group.x, group.y)))
            values = group.turkin1.values
            
            group_x = sorted(groupna.x.unique())
            group_y = sorted(groupna.y.unique())
            group_grid_x, group_grid_y = np.meshgrid(group_x, group_y)
            
            group_grid_z = interpolate.griddata(points,
                                                values,
                                                (group_grid_x, group_grid_y),
                                                method='nearest')
            
            turkin1 = []
            
            for i, j in itertools.product(range(len(group_x)),
                                          range(len(group_y))):
                turkin1.append(group_grid_z[j, i])
            
            groupna = groupna.set_index(["x", "y"])
            groupna = groupna.sort_index()
            groupna["turkin1"] = turkin1
            group = pd.concat([group, groupna.reset_index()])
            
            # Interpolate onto faces grid
            data = collections.defaultdict(list)
            maxf = group[["f0", "f1"]].max().max()
            
            for i in range(maxf + 1):
                
                quad_df = group[(group["f0"] == i) | (group["f1"] == i)]
                quad_df = quad_df.reset_index(drop=True)
                quad_df = quad_df.sort_values(by=['y'], ignore_index=True)
                
                coords = np.array([quad_df.x, quad_df.y]).T
                densities = quad_df.turkin1.values
                target = coords.mean(axis=0)
                
                target_tke = _get_quadrilateral_centre(densities)
                data["x"].append(target[0])
                data["y"].append(target[1])
                data["tke"].append(target_tke)
                
            kdf = pd.DataFrame(data)
            kdf["sigma"] = sigma
            kdf = kdf.set_index(["x", "y", "sigma"])
            
            facest_new = facest_new.combine_first(kdf)
        
        facest_new = facest_new.reset_index()
        facest_new["time"] = time
        faces_final = pd.concat([faces_final, facest_new])
    
    return faces_final[["x",
                        "y",
                        "z",
                        "sigma",
                        "time",
                        "depth",
                        "u",
                        "v",
                        "w",
                        "tke"]]


def _map_to_faces_frame(map_path: StrOrPath,
                        t_step: int = None) -> pd.DataFrame:
    
    data = collections.defaultdict(list)
    
    with xr.open_dataset(map_path) as ds:
        
        if t_step is None:
            t_steps = tuple(range(len(ds.time)))
        else:
            t_steps = (t_step,)
        
        for i in t_steps:
        
            time = ds.time[i].values.take(0)
            x_values = ds.mesh2d_face_x.values
            y_values = ds.mesh2d_face_y.values
            depth_values = ds.mesh2d_waterdepth.values
            sigma_values = ds.mesh2d_layer_sigma.values
            u_values = ds.mesh2d_ucx.values
            v_values = ds.mesh2d_ucy.values
            w_values = ds.mesh2d_ucz.values
            
            for iface in ds.mesh2d_nFaces.values:
                
                x = x_values[iface]
                y = y_values[iface]
                depth = depth_values[i, iface]
                
                for ilayer in ds.mesh2d_nLayers.values:
                    
                    sigma = sigma_values[ilayer]
                    z = sigma * depth
                    u = u_values[i, iface, ilayer]
                    v = v_values[i, iface, ilayer]
                    w = w_values[i, iface, ilayer]
                    
                    data["x"].append(x)
                    data["y"].append(y)
                    data["z"].append(z)
                    data["sigma"].append(sigma)
                    data["time"].append(time)
                    data["depth"].append(depth)
                    data["u"].append(u)
                    data["v"].append(v)
                    data["w"].append(w)
    
    return pd.DataFrame(data)


def _get_quadrilateral_centre(densities: npt.NDArray[np.float64]) -> float:
    return np.sum(0.25 * densities)


class _StructuredFaces(Faces):
    def _get_faces_frame(self, t_step: int) -> pd.DataFrame:
        return  _trim_to_faces_frame(self.nc_path, t_step)


def _trim_to_faces_frame(trim_path: StrOrPath,
                         t_step: int = None) -> pd.DataFrame:
    
    Content = Union[Num, pd.Timestamp]
    data: Dict[str, List[Content]] = collections.defaultdict(list)
    
    with xr.open_dataset(trim_path) as ds:
        
        if t_step is None:
            t_steps = tuple(range(len(ds.time)))
        else:
            t_steps = (t_step,)
        
        for i in t_steps:
            
            time = ds.time[i].values
            ds_step = ds.isel(time=i)
            
            x = ds_step.XZ.values
            y = ds_step.YZ.values
            dp0 = ds_step.DP0.values
            s1 = ds_step.S1.values
            sig_lyr = ds_step.SIG_LYR.values
            ik = ds_step.KMAXOUT_RESTR.values
            u1 = ds_step.U1.values
            v1 = ds_step.V1.values
            w = ds_step.W.values
            tke = ds_step.RTUR1.values
            
            n_layers = len(ik)
            
            x = x[1:-1, 1:-1]
            x = np.repeat(x[np.newaxis, :, :], n_layers, axis=0)
            
            y = y[1:-1, 1:-1]
            y = np.repeat(y[np.newaxis, :, :], n_layers, axis=0)
            
            depth = dp0 + s1
            z = depth[..., None] * sig_lyr
            z = np.rollaxis(z, 2)
            z = z[:, 1:-1, 1:-1]
            
            isig = sig_lyr.reshape(n_layers, 1, 1)
            sigma = np.ones(x.shape, dtype=int) * isig
            
            time = np.tile(time, x.shape)
            
            depth = depth[1:-1, 1:-1]
            depth = np.repeat(depth[np.newaxis, :, :], n_layers, axis=0)
            
            u1 = u1[:, :-1, 1:-1]
            u = np.nansum([u1[:, :-1, :], u1[:, 1:, :]], axis=0) / 2
            
            v1 = v1[:,1:-1,:-1]
            v = np.nansum([v1[:, :, :-1], v1[:, :, 1:]], axis=0) / 2
            
            w = np.nansum([w[1:, :, :], w[:-1, :, :]], axis=0) / 2
            w = w[:, 1:-1, 1:-1]
            
            tke = np.nansum([tke[0, 1:, :, :], tke[0, :-1, :, :]], axis=0) / 2
            tke = tke[:, 1:-1, 1:-1]
            
            data["x"].extend(np.ravel(x))
            data["y"].extend(np.ravel(y))
            data["z"].extend(np.ravel(z))
            data["sigma"].extend(np.ravel(sigma))
            data["time"].extend(np.ravel(time))
            data["depth"].extend(np.ravel(depth))
            data["u"].extend(np.ravel(u))
            data["v"].extend(np.ravel(v))
            data["w"].extend(np.ravel(w))
            data["tke"].extend(np.ravel(tke))
    
    return pd.DataFrame(data)
