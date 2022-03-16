Model Comparison (Windows)
==========================

1 Introduction
--------------

This is a comparison of the performance of simulations of the Mycek
flume experiment (Mycek et al. 2014) using the flexible mesh (FM) and
structured grid solvers for Delft3D. The simulation settings are
mirrored between the two methods as much as possible. The chosen grid
resolution for this study is 0.0625m. Axial and radial velocities in the
horizontal plane intersecting the turbine hub will be examined.

.. _sec:axial:

2 Axial Velocity Comparison
---------------------------

This section compares axial velocities between the FM and structured
grid models. Figs. 1, 2 show the axial velocity over the horizontal
plane intersecting the turbine hub for the FM and structured gird
models, respectively. The units are non-dimensionalised by the
free-stream velocity, measured at the hub location without the presence
of the turbine. If :math:`u` is the dimensional velocity, and
:math:`u_\infty` is the dimensional free stream velocity, then the
normalized velocity :math:`u^* = u / u_\infty`. Note the observable
difference in the wake velocities immediately downstream of the turbine
between the two simulations.

.. figure:: turb_z_u_fm.png
   :alt: Figure 1: Axial velocity normalised by the free stream velocity
         for the fm model type
   :name: fig:turb_z_u_fm
   :width: 3.64in

   Figure 1: Axial velocity normalised by the free stream velocity for
   the fm model type

.. figure:: turb_z_u_structured.png
   :alt: Figure 2: Axial velocity normalised by the free stream velocity
         for the structured model type
   :name: fig:turb_z_u_structured
   :width: 3.64in

   Figure 2: Axial velocity normalised by the free stream velocity for
   the structured model type

Fig. 3 shows the error between the non-dimensional axial velocities of
the structured grid and FM models, relative to the maximum value within
the two simulations. Three main areas of difference are revealed, the
increased deficit in the near wake for the structured model, the reduced
deficit of the structured model in the far wake and the increased
acceleration around the edges of the turbine of the structured model.

.. figure:: turb_z_u_diff.png
   :alt: Figure 3: Relative error in normalised axial velocity between
         the structured and fm models
   :name: fig:turb_z_u_diff
   :width: 3.64in

   Figure 3: Relative error in normalised axial velocity between the
   structured and fm models

Comparing the non-dimensional centerline velocities alongside the
experimental data (published in (Mycek et al. 2014)) in fig. 4, confirms
the behavior in the near and far wake shown in fig. 3. Generally, the
structured model performs better in the near wake compared to the
experimental data, however the performance in the far wake is better for
the FM model, where the wake has decayed less. Nonetheless, neither
model captures the experimental measurements well for the whole
centerline.

.. figure:: transect_u.png
   :alt: Figure 4: Comparison of the normalised turbine centerline
         velocity. Experimental data reverse engineered from (Mycek et al.
         2014, fig. 11a).
   :name: fig:transect_u
   :width: 4in

   Figure 4: Comparison of the normalised turbine centerline velocity.
   Experimental data reverse engineered from (Mycek et al. 2014, fig.
   11a).

.. _sec:radial:

3 Radial Velocity Comparison
----------------------------

This section compares radial velocities between the FM and structured
grid models. Figs. 5, 6 show the radial velocity over the horizontal
plane intersecting the turbine hub for the FM and structured gird
models, respectively. The units are non-dimensionalized by the
free-stream velocity, (in the axial direction) measured at the hub
location without the presence of the turbine. If :math:`v` is the
dimensional velocity, then the normalized velocity
:math:`v^* = v / u_\infty`. Note the increased radial velocities
recorded for the structured grid compared to the FM simulation.

.. figure:: turb_z_v_fm.png
   :alt: Figure 5: Radial velocity normalised by the free stream
         velocity for the fm model type
   :name: fig:turb_z_v_fm
   :width: 3.64in

   Figure 5: Radial velocity normalised by the free stream velocity for
   the fm model type

.. figure:: turb_z_v_structured.png
   :alt: Figure 6: Radial velocity normalised by the free stream
         velocity for the structured model type
   :name: fig:turb_z_v_structured
   :width: 3.64in

   Figure 6: Radial velocity normalised by the free stream velocity for
   the structured model type

Fig. 7 shows the error between the non-dimensional radial velocities of
the structured grid and FM models, relative to the maximum value within
the two simulations. The largest errors are seen upstream of the
turbine, while smaller errors are seen downstream of the turbine. The
errors in the radial flow are also much higher than for the axial flow,
with the maximum error in radial velocity being 0.2425, while the error
is 0.08593 for the axial velocity (from fig. 3).

.. figure:: turb_z_v_diff.png
   :alt: Figure 7: Relative error in normalised radial velocity between
         the structured and fm models
   :name: fig:turb_z_v_diff
   :width: 3.64in

   Figure 7: Relative error in normalised radial velocity between the
   structured and fm models

4 Conclusion
------------

Comparison of simulations of the 2014 Mycek flume experiment (Mycek et
al. 2014) using the flexible mesh (FM) and structured grid solvers for
Delft3D, reveals significant differences. As seen in sec. 2, differences
in the axial velocities between the two methods were seen in the near
wake, far wake, and at the turbine edges. When comparing to the
experimental data, as in fig. 3, it was observed that the structured
grid simulation performs better in the near wake, while the FM
simulation is better in the far wake. In sec. 3, radial velocities were
compared with differences seen immediately upstream and downstream of
the turbine (see fig. 7). Notably, the maximum relative errors between
the two simulations were much larger for the radial velocities than then
axial velocities, 0.2425 and 0.08593 respectively. This discrepancy may
account for some of the differences seen in the axial flows, although
the underlying mechanisms are not yet known. Other factors may also be
contributing, including interpretation of the simulation parameters or
selection of the time step for the structured grid simulations.

References
----------

.. container:: references csl-bib-body hanging-indent
   :name: refs

   .. container:: csl-entry
      :name: ref-mycek2014

      Mycek, Paul, Benoît Gaurier, Grégory Germain, Grégory Pinon, and
      Elie Rivoalen. 2014. “Experimental Study of the Turbulence
      Intensity Effects on Marine Current Turbines Behaviour. Part I:
      One Single Turbine.” *Renewable Energy* 66: 729–46.
      https://doi.org/10.1016/j.renene.2013.12.036.
