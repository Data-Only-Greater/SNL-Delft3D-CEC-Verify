# -*- coding: utf-8 -*-

import os
import shutil
import platform
import warnings
from pathlib import Path
from collections import defaultdict
from dataclasses import replace

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from convergence import Convergence

from snl_d3d_cec_verify import (MycekStudy,
                                Report,
                                Result,
                                LiveRunner,
                                Template,
                                Validate)
from snl_d3d_cec_verify.result import (get_reset_origin,
                                       get_normalised_dims,
                                       get_normalised_data,
                                       get_normalised_data_deficit)
from snl_d3d_cec_verify.text import Spinner

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


def get_u0(da, case, transect, factor):
    
    da = get_reset_origin(da,
                          (case.turb_pos_x, case.turb_pos_y, case.turb_pos_z))
    da = get_normalised_dims(da, transect.attrs["$D$"])
    da = get_normalised_data(da, factor)
    
    return da


def get_gamma0(da, case, transect):
    
    da = get_reset_origin(da,
                          (case.turb_pos_x, case.turb_pos_y, case.turb_pos_z))
    da = get_normalised_dims(da, transect.attrs["$D$"])
    da = get_normalised_data_deficit(da,
                                     transect.attrs["$U_\\infty$"],
                                     "$\gamma_0$")
    
    return da


def plot_transects(case,
                   validate,
                   result,
                   factor,
                   ustar_ax,
                   gamma_ax):
    
    for i, transect in enumerate(validate):
        
        transect_true = transect.to_xarray()
        
        # Compare transect
        transect_sim = result.faces.extract_z(-1, **transect)
        
        # Determine plot x-axis
        major_axis = f"${transect.attrs['major_axis']}^*$"
        
        # Create and save a u0 figure
        transect_sim_u0 = get_u0(transect_sim["$u$"],
                                 case,
                                 transect_true,
                                 factor)
        
        transect_sim_u0.plot(ax=ustar_ax[i],
                             x=major_axis,
                             label=f'{case.dx}m')
        
        # Create and save a gamma0 figure
        transect_sim_gamma0 = get_gamma0(transect_sim["$u$"],
                                         case,
                                         transect_true)
        
        transect_sim_gamma0.plot(ax=gamma_ax[i],
                                 x=major_axis,
                                 label=f'{case.dx}m')



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

max_experiments = 5
omp_num_threads = 8

grid_resolution = [1 / 2 ** i for i in range(max_experiments)]
sigma = [int(2 / delta) for delta in grid_resolution]
stats_interval = [240 / (k ** 2) for k in sigma]

cases = MycekStudy(dx=grid_resolution,
                   dy=grid_resolution,
                   sigma=sigma,
                   x0=4,
                   x1=8,
                   stats_interval=stats_interval,
                   restart_interval=600)
template = Template()
runner = LiveRunner(get_d3d_bin_path(),
                    omp_num_threads=omp_num_threads)

u_infty_data = defaultdict(list)
u_wake_data = defaultdict(list)
u_infty_convergence = Convergence()
u_wake_convergence = Convergence()

case_counter = 0
asymptotic_range = False

run_directory = Path("production_runs")
run_directory.mkdir(exist_ok=True)

report = Report(79, "%d %B %Y")
report_dir = Path("production_report")
report_dir.mkdir(exist_ok=True)

global_validate = Validate()
ustar_figs = []
ustar_axs = []
gamma_figs = []
gamma_axs = []

for _ in global_validate:
    ustar_fig, ustar_ax = plt.subplots(figsize=(4, 2.75), dpi=300)
    gamma_fig, gamma_ax = plt.subplots(figsize=(4, 2.75), dpi=300)
    ustar_figs.append(ustar_fig)
    ustar_axs.append(ustar_ax)
    gamma_figs.append(gamma_fig)
    gamma_axs.append(gamma_ax)


while True:
    
    if case_counter + 1 > len(cases):
        break
    
    case = cases[case_counter]
    no_turb_case = replace(case, simulate_turbines=False)
    validate = Validate(case)
    
    section = f"{case.dx}m Resolution"
    print(section)
    
    no_turb_dir = run_directory / f"no_turbine_{case.dx}"
    
    if no_turb_dir.is_dir():
        try:
            Result(no_turb_dir)
        except FileNotFoundError:
            shutil.rmtree(no_turb_dir)
    
    # Determine $U_\infty$ for case, by running without the turbine
    if not no_turb_dir.is_dir():
        
        print("Simulating without turbine")
        
        no_turb_dir.mkdir()
        
        template(no_turb_case, no_turb_dir)
        
        with Spinner() as spin:
            for line in runner(no_turb_dir):
                spin(line)
    
    result = Result(no_turb_dir)
    
    u_infty_ds = result.faces.extract_turbine_centre(-1, no_turb_case)
    u_infty = u_infty_ds["$u$"].values.take(0)
    
    u_infty_data["resolution (m)"].append(case.dx)
    u_infty_data["value (m/s)"].append(u_infty)
    
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore",
                                message="Insufficient grids for analysis")
        u_infty_convergence.add_grids([(case.dx, u_infty)])
    
    turb_dir = run_directory / f"turbine_{case.dx}"
    
    if turb_dir.is_dir():
        try:
            Result(turb_dir)
        except FileNotFoundError:
            shutil.rmtree(turb_dir)
    
    # Run with turbines
    if not turb_dir.is_dir():
        
        print("Simulating with turbine")
        
        turb_dir.mkdir()
        
        template(case, turb_dir)
        
        with Spinner() as spin:
            for line in runner(turb_dir):
                spin(line)
    
    result = Result(turb_dir)
    
    # Collect wake velocity at 1.2D downstream
    u_wake_ds = result.faces.extract_turbine_centre(-1,
                                                    case,
                                                    offset_x=0.84)
    u_wake = u_wake_ds["$u$"].values.take(0)
    
    u_wake_data["resolution (m)"].append(case.dx)
    u_wake_data["value (m/s)"].append(u_wake)
    
    # Record
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore",
                                message="Insufficient grids for analysis")
        u_wake_convergence.add_grids([(case.dx, u_wake)])
    
    plot_transects(case, validate, result, u_infty, ustar_axs, gamma_axs)
    
    case_counter += 1
    
    if case_counter < 3: continue
    
    # print(u_infty_convergence[0].asymptotic_ratio)
    # print(u_wake_convergence[0].asymptotic_ratio)
    
    if abs(1 - u_wake_convergence[0].asymptotic_ratio) < 0.01:
        asymptotic_range = True
        break
    
    if case_counter == max_experiments:
        break


for i, transect in enumerate(global_validate):
    
    transect_true = transect.to_xarray()
    major_axis = f"${transect.attrs['major_axis']}^*$"
    
    transect_true_u0 = get_u0(transect_true, case, transect_true, 0.8)
    transect_true_u0.plot(ax=ustar_axs[i], x=major_axis, label='Experiment')
    
    ustar_axs[i].legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ustar_axs[i].grid()
    ustar_axs[i].set_title("")
    
    plot_name = f"transect_u0_{i}.png"
    plot_path = report_dir / plot_name
    ustar_figs[i].savefig(plot_path, bbox_inches='tight')
    
    # Add figure with caption
    caption = ("Normalised turbine centreline velocity, $u^*_0$, "
               "comparison (m/s). Experimental data reverse engineered "
               f"from [@mycek2014, fig. {transect.attrs['figure']}].")
    report.content.add_image(plot_name, caption, width="4in")
    
    transect_true_gamma0 = get_gamma0(transect_true,
                                      case,
                                      transect_true)
    transect_true_gamma0.plot(ax=gamma_axs[i],
                              x=major_axis,
                              label='Experiment')
    
    gamma_axs[i].legend(loc='center left', bbox_to_anchor=(1, 0.5))
    gamma_axs[i].grid()
    gamma_axs[i].set_title("")
    
    plot_name = f"transect_gammm0_{i}.png"
    plot_path = report_dir / plot_name
    gamma_figs[i].savefig(plot_path, bbox_inches='tight')
    
    # Add figure with caption
    caption = ("Normalised turbine centreline velocity deficit, "
               "$\gamma_0$, comparison (%). Experimental data reverse "
               "engineered from [@mycek2014, fig. "
               f"{transect.attrs['figure']}].")
    report.content.add_image(plot_name, caption, width="4in")


u_infty_df = pd.DataFrame(u_infty_data)
u_wake_df = pd.DataFrame(u_wake_data)

print(u_infty_df)
print(u_wake_df)

print(asymptotic_range)
print(u_wake_convergence[0].fine.gci_fine)
print(u_wake_convergence.get_resolution(0.01))

# Add section for the references
report.content.add_heading("References", level=2)

# Add report metadata
os_name = platform.system()
report.title = f"Validation Example ({os_name})"
report.date = "today"

# Write the report to file
with open(report_dir / "report.md", "wt") as f:
    for line in report:
        f.write(line)

# Convert file to docx or print report to stdout
try:
    
    import pypandoc
    
    pypandoc.convert_file(f"{report_dir / 'report.md'}",
                          'docx',
                          outputfile=f"{report_dir / 'report.docx'}",
                          extra_args=['-C',
                                      f'--resource-path={report_dir}',
                                      '--bibliography=validation.bib',
                                      '--reference-doc=reference.docx'])

except ImportError:
    
    print(report)