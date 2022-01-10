# -*- coding: utf-8 -*-

import os
import platform
import tempfile
from pathlib import Path
from collections import defaultdict
from dataclasses import replace

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from snl_d3d_cec_verify import (MycekStudy,
                                Report,
                                Result,
                                Runner,
                                Template,
                                Validate)
from snl_d3d_cec_verify.result import (get_reset_origin,
                                       get_normalised_dims,
                                       get_normalised_data_deficit)

matplotlib.rcParams.update({'font.size': 8})


def get_d3d_bin_path():
    
    env = dict(os.environ)
    
    if 'D3D_BIN' in env:
        root = Path(env['D3D_BIN'].replace('"', ''))
        print('D3D_BIN found')
    else:
        root = Path("..") / "src" / "bin"
        print('D3D_BIN not found')
    
    print(f'Setting bin folder path to {root.resolve()}')
    
    return root.resolve()


def get_u0(da, case, transect):
    
    da = get_reset_origin(da,
                          (case.turb_pos_x, case.turb_pos_y, case.turb_pos_z))
    da = get_normalised_dims(da, transect.attrs["$D$"])
    
    return da


def get_gamma0(da, case, transect):
    
    da = get_reset_origin(da,
                          (case.turb_pos_x, case.turb_pos_y, case.turb_pos_z))
    da = get_normalised_dims(da, transect.attrs["$D$"])
    da = get_normalised_data_deficit(da,
                                     transect.attrs["$U_\\infty$"],
                                     "$\gamma_0$")
    
    return da


def get_rmse(estimated, observed):
    return np.sqrt(((estimated - observed) ** 2).mean())

# Steps:
#
# 1. Define a series of grid studies, doubling resolution
# 2. Iterate
# 3. Determine U_\infty by running without turbines
# 4. Run with turbines
# 5. Record results
# 6. After 3 runs record asymptotic ratio
# 7. If in asymptotic range stop iterating
# 8. Calculate resolution at desired GCI
# 9. Compute at desired resolution if lower than last iteration
# 10. Make report

max_experiments = 2 #5
omp_num_threads = 6

grid_resolution = [1 / 2 ** i for i in range(max_experiments)]
sigma = [int(2 / delta) for delta in grid_resolution]

cases = MycekStudy(dx=grid_resolution, dy=grid_resolution, sigma=sigma)
template = Template()
runner = Runner(get_d3d_bin_path(),
                omp_num_threads=omp_num_threads)

u_infty_data = defaultdict(list)
u_wake_data = defaultdict(list)

case_counter = 0

while True:
    
    case = cases[case_counter]
    no_turb_case = replace(case, simulate_turbines=False)
    
    # Determine $U_\infty$ for case, by running without the turbine
    with tempfile.TemporaryDirectory() as tmpdirname:
        
        template(no_turb_case, tmpdirname)
        runner(tmpdirname)
        result = Result(tmpdirname)
        
        u_infty_ds = result.faces.extract_turbine_centre(-1, no_turb_case)
        u_infty = u_infty_ds["$u$"].values.take(0)
        
        u_infty_data["resolution (m)"].append(case.dx)
        u_infty_data["value (m/s)"].append(u_infty)
    
    # Run with turbines
    with tempfile.TemporaryDirectory() as tmpdirname:
        
        template(case, tmpdirname)
        runner(tmpdirname)
        result = Result(tmpdirname)
        
        # Collect wake velocity at 1.2D downstream
        u_wake_ds = result.faces.extract_turbine_centre(-1,
                                                        case,
                                                        offset_x=0.84)
        u_wake = u_wake_ds["$u$"].values.take(0)
        
        u_wake_data["resolution (m)"].append(case.dx)
        u_wake_data["value (m/s)"].append(u_wake)
    
    case_counter += 1
    
    if case_counter == max_experiments:
        break

u_infty_df = pd.DataFrame(u_infty_data)
u_wake_df = pd.DataFrame(u_wake_data)

print(u_infty_df)
print(u_wake_df)
