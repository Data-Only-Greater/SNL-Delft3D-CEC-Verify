# -*- coding: utf-8 -*-

from __future__ import annotations

import collections
from typing import (cast,
                    Dict,
                    Optional,
                    Sequence)
from functools import wraps
from dataclasses import dataclass, field

import numpy as np
import pandas as pd # type: ignore
import xarray as xr

from .base import TimeStepResolver
from ..cases import CaseStudy
from ..types import Num, StrOrPath
from .._docs import docstringtemplate


# TODO: I'd like to type check this, but I can't get it to work.
def _extract(method):
    
    @wraps(method)
    def magic(self, t_step: int,
                    kz: Num,
                    x: Optional[Sequence[Num]] = None,
                    y: Optional[Sequence[Num]] = None) -> xr.Dataset:
        
        do_interp = sum((bool(x is not None),
                         bool(y is not None)))
        
        if do_interp == 1:
            raise RuntimeError("x and y must both be set")
        
        t_step = self._resolve_t_step(t_step)
        
        if t_step not in self._t_steps:
            self._load_t_step(t_step)
        
        ds = method(self, t_step, kz)
        
        if not do_interp: return ds
        
        return ds.interp({"$x$": xr.DataArray(x),
                          "$y$": xr.DataArray(y)})
        
    return magic


@dataclass
class Faces(TimeStepResolver):
    """Class for extracting results on the faces of the simulation grid. Use in
    conjunction with the :class:`.Result` class.
    
    >>> from snl_d3d_cec_verify import Result
    >>> data_dir = getfixture('data_dir')
    >>> result = Result(data_dir)
    >>> result.faces.extract_z(-1, -1) #doctest: +ELLIPSIS
    <xarray.Dataset>
    Dimensions:  ($x$: 18, $y$: 4)
    Coordinates:
      * $x$      ($x$) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
      * $y$      ($y$) float64 1.5 2.5 3.5 4.5
        $z$      ... -1
        time     datetime64[ns] 2001-01-01T01:00:00
    Data variables:
        k        ($x$, $y$) float64 1.002 1.002 1.002 1.002 ... 1.0 1.0 1.0 1.0
        $u$      ($x$, $y$) float64 0.781 0.781 0.781 0.781 ... 0.7763 0.7763 0.7763
        $v$      ($x$, $y$) float64 -3.237e-18 1.423e-17 ... -8.598e-17 -4.824e-17
        $w$      ($x$, $y$) float64 -0.01472 -0.01472 -0.01472 ... 0.001343 0.001343
        
    :param map_path: path to the :code:`FlowFM_map.nc` file
    :param n_steps: number of time steps in the simulation
    :param xmax: Maximum of x-direction range, in metres
    
    """
    
    xmax: Num #: Maximum of x-direction range, in metres
    _t_steps: Dict[int, pd.Timestamp] = field(default_factory=dict,
                                              init=False,
                                              repr=False)
    _frame: Optional[pd.DataFrame] = field(default=None,
                                           init=False,
                                           repr=False)
    
    @docstringtemplate
    def extract_turbine_centre(self, t_step: int,
                                     case: CaseStudy,
                                     offset_x: Num = 0,
                                     offset_y: Num = 0,
                                     offset_z: Num = 0) -> xr.Dataset:
        """Extract data at the turbine centre, as defined in the given
        :class:`.CaseStudy` object. Available data is:
        
        * :code:`k`: sigma layer
        * :code:`u`: velocity in the x-direction, in metres per second
        * :code:`v`: velocity in the x-direction, in metres per second
        * :code:`w`: velocity in the x-direction, in metres per second
        
        Results are returned as a :class:`xarray.Dataset`. For example:
        
        >>> from snl_d3d_cec_verify import MycekStudy, Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> case = MycekStudy()
        >>> result.faces.extract_turbine_centre(-1, case) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:  (dim_0: 1)
        Coordinates:
            $z$      ... -1
            time     datetime64[ns] 2001-01-01T01:00:00
            $x$      (dim_0) ... 6
            $y$      (dim_0) ... 3
        Dimensions without coordinates: dim_0
        Data variables:
            k        (dim_0) float64 1.001
            $u$      (dim_0) float64 0.7748
            $v$      (dim_0) float64 -2.942e-17
            $w$      (dim_0) float64 0.0002786
        
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
        
        Results are returned as a :class:`xarray.Dataset`. Use the ``x_step``
        argument to control the frequency of samples. For example:
        
        >>> from snl_d3d_cec_verify import MycekStudy, Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> case = MycekStudy()
        >>> result.faces.extract_turbine_centreline(-1, case, x_step=1) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:  (dim_0: 13)
        Coordinates:
            $z$      ... -1
            time     datetime64[ns] 2001-01-01T01:00:00
            $x$      (dim_0) float64 6.0 7.0 8.0 9.0 10.0 ... 14.0 15.0 16.0 17.0 18.0
            $y$      (dim_0) ... 3 3 3 3 3 3 3 3 3 3 3 3 3
        Dimensions without coordinates: dim_0
        Data variables:
            k        (dim_0) float64 1.001 1.001 1.001 1.001 1.001 ... 1.0 1.0 1.0 nan
            $u$      (dim_0) float64 0.7748 0.7747 0.7745 0.7745 ... 0.7759 0.7762 nan
            $v$      (dim_0) float64 -2.942e-17 4.192e-17 9.126e-17 ... -8.523e-17 nan
            $w$      (dim_0) float64 0.0002786 -0.0004764 0.0003097 ... -7.294e-05 nan
        
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
        
        return self.extract_z(t_step, turb_pos_z + offset_z, x, y)
    
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
        
        Results are returned as a :class:`xarray.Dataset`.For example:
        
        >>> from snl_d3d_cec_verify import MycekStudy, Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> case = MycekStudy()
        >>> result.faces.extract_turbine_z(-1, case) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:  ($x$: 18, $y$: 4)
        Coordinates:
          * $x$      ($x$) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
          * $y$      ($y$) float64 1.5 2.5 3.5 4.5
            $z$      ... -1
            time     datetime64[ns] 2001-01-01T01:00:00
        Data variables:
            k        ($x$, $y$) float64 1.002 1.002 1.002 1.002 ... 1.0 1.0 1.0 1.0
            $u$      ($x$, $y$) float64 0.781 0.781 0.781 0.781 ... 0.7763 0.7763 0.7763
            $v$      ($x$, $y$) float64 -3.237e-18 1.423e-17 ... -8.598e-17 -4.824e-17
            $w$      ($x$, $y$) float64 -0.01472 -0.01472 -0.01472 ... 0.001343 0.001343
        
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
                        z: Num) -> xr.Dataset:
        """Extract data on the plane at the given z-level. Available data is:
        
        * :code:`k`: sigma layer
        * :code:`u`: velocity in the x-direction, in metres per second
        * :code:`v`: velocity in the x-direction, in metres per second
        * :code:`w`: velocity in the x-direction, in metres per second
        
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
        Dimensions:  (dim_0: 5)
        Coordinates:
            $z$      ... -1
            time     datetime64[ns] 2001-01-01T01:00:00
            $x$      (dim_0) ... 6 7 8 9 10
            $y$      (dim_0) ... 2 2 2 2 2
        Dimensions without coordinates: dim_0
        Data variables:
            k        (dim_0) float64 1.001 1.001 1.001 1.001 1.001
            $u$      (dim_0) float64 0.7748 0.7747 0.7745 0.7745 0.7746
            $v$      (dim_0) float64 -3.877e-18 4.267e-17 5.452e-17 5.001e-17 8.011e-17
            $w$      (dim_0) float64 0.0002786 -0.0004764 0.0003097 -0.0002754 0.0003252
        
        If ``x`` and ``y`` are not given, then the results are returned at the
        face centres.
        
        >>> result.faces.extract_z(-1, -1) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:  ($x$: 18, $y$: 4)
        Coordinates:
          * $x$      ($x$) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
          * $y$      ($y$) float64 1.5 2.5 3.5 4.5
            $z$      ... -1
            time     datetime64[ns] 2001-01-01T01:00:00
        Data variables:
            k        ($x$, $y$) float64 1.002 1.002 1.002 1.002 ... 1.0 1.0 1.0 1.0
            $u$      ($x$, $y$) float64 0.781 0.781 0.781 0.781 ... 0.7763 0.7763 0.7763
            $v$      ($x$, $y$) float64 -3.237e-18 1.423e-17 ... -8.598e-17 -4.824e-17
            $w$      ($x$, $y$) float64 -0.01472 -0.01472 -0.01472 ... 0.001343 0.001343
        
        :param t_step: Time step index
        :param z: z-level at which to extract data
        :param x: x-coordinates on which to interpolate data
        :type x: Optional[Sequence[Union[int, float]]]
        :param y: y-coordinates on which to interpolate data
        :type y: Optional[Sequence[Union[int, float]]]
        
        :raises IndexError: if the time-step index (``t_step``) is out of
            range
        :raises RuntimeError: if only ``x`` or ``y`` is set
        
        :rtype: xarray.Dataset
        
        """
        
        return _faces_frame_to_slice(self._frame,
                                     self._t_steps[t_step],
                                     z=z)
    
    @_extract
    def extract_k(self, t_step: int,
                        k: int) -> xr.Dataset:
        """Extract data on the plane at the given sigma-level (k). Available
        data is:
        
        * :code:`z`: the z-level, in metres
        * :code:`u`: velocity in the x-direction, in metres per second
        * :code:`v`: velocity in the x-direction, in metres per second
        * :code:`w`: velocity in the x-direction, in metres per second
        
        Results are returned as a :class:`xarray.Dataset`. If the ``x`` and 
        ``y`` parameters are defined, then the results are interpolated onto
        the given coordinates. For example:
        
        >>> from snl_d3d_cec_verify import Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> x = [6, 7, 8, 9, 10]
        >>> y = [2, 2, 2, 2, 2]
        >>> result.faces.extract_k(-1, 1, x, y) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:  (dim_0: 5)
        Coordinates:
            k        ... 1
            time     datetime64[ns] 2001-01-01T01:00:00
            $x$      (dim_0) ... 6 7 8 9 10
            $y$      (dim_0) ... 2 2 2 2 2
        Dimensions without coordinates: dim_0
        Data variables:
            $z$      (dim_0) float64 -1.001 -1.001 -1.001 -1.001 -1.001
            $u$      (dim_0) float64 0.7747 0.7746 0.7744 0.7745 0.7745
            $v$      (dim_0) float64 -3.88e-18 4.267e-17 5.452e-17 5.002e-17 8.013e-17
            $w$      (dim_0) float64 0.0002791 -0.0004769 0.0003101 -0.0002756 0.0003256
        
        If ``x`` and ``y`` are not given, then the results are returned at the
        face centres.
        
        >>> result.faces.extract_k(-1, 1) #doctest: +ELLIPSIS
        <xarray.Dataset>
        Dimensions:  ($x$: 18, $y$: 4)
        Coordinates:
          * $x$      ($x$) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
          * $y$      ($y$) float64 1.5 2.5 3.5 4.5
            k        ... 1
            time     datetime64[ns] 2001-01-01T01:00:00
        Data variables:
            $z$      ($x$, $y$) float64 -1.001 -1.001 -1.001 -1.001 ... -1.0 -1.0 -1.0
            $u$      ($x$, $y$) float64 0.7809 0.7809 0.7809 ... 0.7763 0.7763 0.7763
            $v$      ($x$, $y$) float64 -3.29e-18 1.419e-17 ... -8.598e-17 -4.824e-17
            $w$      ($x$, $y$) float64 -0.01473 -0.01473 -0.01473 ... 0.001343 0.001343
        
        :param t_step: Time step index
        :param k: k-level (sigma) at which to extract data
        :param x: x-coordinates on which to interpolate data
        :type x: Optional[Sequence[Union[int, float]]]
        :param y: y-coordinates on which to interpolate data
        :type y: Optional[Sequence[Union[int, float]]]
        
        :raises IndexError: if the time-step index (``t_step``) is out of
            range
        :raises RuntimeError: if only ``x`` or ``y`` is set
        
        :rtype: xarray.Dataset
        
        """
        
        return _faces_frame_to_slice(self._frame,
                                     self._t_steps[t_step],
                                     k=k)
    
    def extract_depth(self, t_step: int) -> xr.DataArray:
        """Extract the depth, in meters, at each of the face centres.
        
        Results are returned as a :class:`xarray.DataArray`. For example:
        
        >>> from snl_d3d_cec_verify import Result
        >>> data_dir = getfixture('data_dir')
        >>> result = Result(data_dir)
        >>> result.faces.extract_depth(-1)
        <xarray.DataArray 'depth' (x: 18, y: 4)>
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
          * x        (x) float64 0.5 1.5 2.5 3.5 4.5 5.5 ... 13.5 14.5 15.5 16.5 17.5
          * y        (y) float64 1.5 2.5 3.5 4.5
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
        
        frame = _map_to_faces_frame(self.map_path, t_step)
        
        if self._frame is None:
            self._frame = frame
        else:
            self._frame = self._frame.append(frame,
                                             ignore_index=True,
                                             sort=False)
        
        self._t_steps[t_step] = pd.Timestamp(frame["time"].unique().take(0))


def _check_case_study(case: CaseStudy):
    if len(case) != 1:
        raise ValueError("case study must have length one")


def _map_to_faces_frame(map_path: StrOrPath,
                       t_step: int = None) -> pd.DataFrame:
    
    data = collections.defaultdict(list)
    
    with xr.open_dataset(map_path) as ds:
        
        time = ds.time[t_step].values.take(0)
        
        for iface in ds.mesh2d_nFaces.values:
            
            x = ds.mesh2d_face_x[iface].values.take(0)
            y = ds.mesh2d_face_y[iface].values.take(0)
            depth = ds.mesh2d_waterdepth[t_step, iface].values.take(0)
            
            for k, ilayer in enumerate(ds.mesh2d_nLayers.values):
                
                z = ds.mesh2d_layer_sigma[ilayer].values * \
                                ds.mesh2d_waterdepth[t_step, iface].values
                u = ds.mesh2d_ucx[t_step, iface, ilayer].values.take(0)
                v = ds.mesh2d_ucy[t_step, iface, ilayer].values.take(0)
                w = ds.mesh2d_ucz[t_step, iface, ilayer].values.take(0)
                
                data["x"].append(x)
                data["y"].append(y)
                data["z"].append(z)
                data["k"].append(k)
                data["time"].append(time)
                data["depth"].append(depth)
                data["u"].append(u)
                data["v"].append(v)
                data["w"].append(w)
    
    return pd.DataFrame(data)


def _faces_frame_to_slice(frame: pd.DataFrame,
                          sim_time: pd.Timestamp,
                          k: Optional[int] = None,
                          z: Optional[Num] = None) -> xr.Dataset:
    
    if (k is None and z is None) or (k is not None and z is not None):
        raise RuntimeError("either k or z must be given")
    
    frame = frame.set_index(['x', 'y', 'z', 'time'])
    frame = frame.xs(sim_time, level=3)
    
    if z is None:
        
        kframe = frame[frame["k"] == k]
        kframe = kframe.drop(["depth", "k"], axis=1)
        kframe = kframe.reset_index(2)
        ds = kframe.to_xarray()
        ds = ds.assign_coords({"k": k})
    
    else:
        
        data = collections.defaultdict(list)
        
        for (x, y), group in frame.groupby(level=[0, 1]):
            
            gframe = group.droplevel([0, 1])
            zvalues = gframe.reindex(
                        gframe.index.union([z])).interpolate('values').loc[z]
            
            data["x"].append(x)
            data["y"].append(y)
            data["k"].append(zvalues["k"])
            data["u"].append(zvalues["u"])
            data["v"].append(zvalues["v"])
            data["w"].append(zvalues["w"])
            
        zframe = pd.DataFrame(data)
        zframe = zframe.set_index(['x', 'y'])
        ds = zframe.to_xarray()
        ds = ds.assign_coords({"z": z})
    
    ds = ds.assign_coords({"time": sim_time})
    ds = ds.rename({"z": "$z$",
                    "x": "$x$",
                    "y": "$y$",
                    "u": "$u$",
                    "v": "$v$",
                    "w": "$w$"})
    
    return ds


def _faces_frame_to_depth(frame: pd.DataFrame,
                         sim_time: pd.Timestamp) -> xr.DataArray:
    
    frame = frame.set_index(['x', 'y', 'k', 'time'])
    frame = frame.xs((0, sim_time), level=(2, 3))
    frame = frame.drop(["z", "u", "v", "w"], axis=1)
    ds = frame.to_xarray()
    ds = ds.assign_coords({"time": sim_time})
    
    return ds.depth
