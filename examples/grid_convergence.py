# -*- coding: utf-8 -*-

import os
import uuid
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


def main(template_type, max_experiments, omp_num_threads):
    
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
    
    # Set grid resolutions and reporting times
    grid_resolution = [1 / 2 ** i for i in range(max_experiments)]
    sigma = [int(2 / delta) for delta in grid_resolution]
    
    kwargs = {"dx": grid_resolution,
              "dy": grid_resolution,
              "sigma": sigma,
              "restart_interval": 600}
    
    # Choose options based on the template type
    if template_type == "fm":
        
        kwargs["stats_interval"] = [240 / (k ** 2) for k in sigma]
    
    elif template_type == "structured":
        
        # Set time step based on flexible mesh runs
        dt_init_all = [0.5, 0.25, 0.1, 0.0375, 0.0125]
        kwargs["dt_init"] = dt_init_all[:max_experiments]
    
    else:
        
        raise ValueError(f"Template type '{template_type}' unrecognised")
    
    cases = MycekStudy(**kwargs)
    template = Template(template_type)
    
    # Use the LiveRunner class to get real time feedback from the Delft3D
    # calculation
    runner = LiveRunner(get_d3d_bin_path(),
                        omp_num_threads=omp_num_threads)
    
    u_infty_data = defaultdict(list)
    u_wake_data = defaultdict(list)
    ti_wake_data = defaultdict(list)
    transect_data = defaultdict(list)
    u_infty_convergence = Convergence()
    u_wake_convergence = Convergence()
    ti_wake_convergence = Convergence()
    
    case_counter = 0
    
    run_directory = Path(template_type) / "runs"
    run_directory.mkdir(exist_ok=True, parents=True)
    
    report = Report(79, "%d %B %Y")
    report_dir = Path(template_type) / "grid_convergence_report"
    report_dir.mkdir(exist_ok=True, parents=True)
    
    global_validate = Validate()
    ustar_figs = []
    ustar_axs = []
    gamma_figs = []
    gamma_axs = []
    
    for _ in global_validate:
        ustar_fig, ustar_ax = plt.subplots(figsize=(5, 3.5), dpi=300)
        gamma_fig, gamma_ax = plt.subplots(figsize=(5, 3.5), dpi=300)
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
        ncells = get_cells(case)
        
        section = f"{case.dx}m Resolution"
        print(section)
        
        no_turb_dir = find_project_dir(run_directory, no_turb_case)
        
        if no_turb_dir is not None:
            try:
                Result(no_turb_dir)
                print("Loading pre-existing simulation at path "
                      f"'{no_turb_dir}'")
            except FileNotFoundError:
                no_turb_dir = None
        
        # Determine $U_\infty$ for case, by running without the turbine
        if no_turb_dir is None:
            
            print("Simulating without turbine")
            
            no_turb_dir = get_unique_dir(run_directory)
            no_turb_dir.mkdir()
            
            template(no_turb_case, no_turb_dir)
            case_path = no_turb_dir / "case.yaml"
            no_turb_case.to_yaml(case_path)
            
            with Spinner() as spin:
                for line in runner(no_turb_dir):
                    spin(line)
        
        result = Result(no_turb_dir)
        
        u_infty_ds = result.faces.extract_turbine_centre(-1, no_turb_case)
        u_infty = u_infty_ds["$u$"].values.take(0)
        
        u_infty_data["resolution (m)"].append(case.dx)
        u_infty_data["# cells"].append(ncells)
        u_infty_data["$U_\\infty$"].append(u_infty)
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore",
                                    message="Insufficient grids for analysis")
            u_infty_convergence.add_grids([(case.dx, u_infty)])
        
        turb_dir = find_project_dir(run_directory, case)
        
        if turb_dir is not None:
            try:
                Result(turb_dir)
                print(f"Loading pre-existing simulation at path '{turb_dir}'")
            except FileNotFoundError:
                turb_dir = None
        
        # Run with turbines
        if turb_dir is None:
            
            print("Simulating with turbine")
            
            turb_dir = get_unique_dir(run_directory)
            turb_dir.mkdir()
            
            template(case, turb_dir)
            case_path = turb_dir / "case.yaml"
            case.to_yaml(case_path)
            
            with Spinner() as spin:
                for line in runner(turb_dir):
                    spin(line)
        
        result = Result(turb_dir)
        
        # Collect wake data at 1.2D downstream
        wake_ds = result.faces.extract_turbine_centre(-1,
                                                      case,
                                                      offset_x=0.84)
        
        # Velocity
        u_wake = wake_ds["$u$"].values.take(0)
        u_wake_data["resolution (m)"].append(case.dx)
        u_wake_data["# cells"].append(ncells)
        u_wake_data["$U_{1.2D}$"].append(u_wake)
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore",
                                    message="Insufficient grids for analysis")
            u_wake_convergence.add_grids([(case.dx, u_wake)])
        
        # TI
        ti_wake_ds = wake_ds.assign({"$I$": get_TI})
        ti_wake = ti_wake_ds["$I$"].values.take(0)
        
        ti_wake_data["resolution (m)"].append(case.dx)
        ti_wake_data["# cells"].append(ncells)
        ti_wake_data["$k_{1.2D}$"].append(ti_wake)
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore",
                                    message="Insufficient grids for analysis")
            ti_wake_convergence.add_grids([(case.dx, ti_wake)])
        
        plot_transects(case, validate, result, u_infty, ustar_axs, gamma_axs)
        get_transect_error(case,
                           validate,
                           result,
                           u_infty,
                           transect_data)
        
        case_counter += 1
        
        if case_counter < 3: continue
        
        if abs(1 - u_wake_convergence[0].asymptotic_ratio) < 0.01:
            break
        
        if case_counter == max_experiments:
            break
    
    gci_required = 0.01
    
    u_infty_exact = u_infty_convergence[0].fine.f_exact
    u_infty_gci = u_infty_convergence.get_resolution(gci_required)
    err = [abs((f0 / u_infty_exact) - 1) for f0 in u_infty_data["$U_\\infty$"]]
    u_infty_data["error"] = err
    u_infty_df = pd.DataFrame(u_infty_data)
    
    u_wake_exact = u_wake_convergence[0].fine.f_exact
    u_wake_gci = u_wake_convergence.get_resolution(gci_required)
    err = [abs((f0 / u_wake_exact) - 1) for f0 in u_wake_data["$U_{1.2D}$"]]
    u_wake_data["error"] = err
    u_wake_df = pd.DataFrame(u_wake_data)
    
    gamma0_sim = 100 * (1 - u_wake_exact / u_infty_exact)
    centreline = global_validate[0]
    gamma0_true = 100 * (1 - centreline.data[0] /
                                             centreline.attrs["$U_\infty$"])
    gamma0_err = abs((gamma0_sim - gamma0_true) / gamma0_true)
    
    ti_wake_exact = ti_wake_convergence[0].fine.f_exact
    ti_wake_gci = ti_wake_convergence.get_resolution(gci_required)
    err = [abs((f0 / ti_wake_exact) - 1) for f0 in ti_wake_data["$k_{1.2D}$"]]
    ti_wake_data["error"] = err
    ti_wake_df = pd.DataFrame(ti_wake_data)
    
    transect_df = pd.DataFrame(transect_data)
    transect_grouped = transect_df.groupby(["Transect"])
    
    transect_summary = ""
    n_transects = len(global_validate)
    
    lower_first = lambda s: s[:1].lower() + s[1:] if s else ''
    
    for i, transect in enumerate(global_validate):
        
        if transect.name not in ["$u$", "$u_0$"]: continue
        
        description = transect.attrs['description']
        transect_df = transect_grouped.get_group(description).drop("Transect",
                                                                   axis=1)
        transect_rmse = transect_df.iloc[-1, 1]
        
        transect_summary += (
            f"For the {lower_first(description)} transect, the root mean "
            "square error at the lowest grid resolution was "
            f"{transect_rmse:.4g}.")
        
        if (i + 1) < n_transects:
            transect_summary += " "
    
    report.content.add_heading("Summary", level=2)
    
    summary_text = (
        f"This is a grid convergence study of {len(cases)} cases. The "
        f"case with the finest grid resolution, of {case.dx}m, achieved an "
        f"asymptotic ratio of {u_wake_convergence[0].asymptotic_ratio:.4g} "
        "(asymptotic range is indicated by a value $\\approx 1$). At zero "
        "grid resolution, the normalised velocity deficit measured 1.2 "
        f"diameters downstream from the turbine was {gamma0_sim:.4g}\%, a "
        f"{gamma0_err * 100:.4g}\% error against the measured value of "
        f"{gamma0_true:.4g}\%. ")
    summary_text += transect_summary
    
    report.content.add_text(summary_text)
    
    report.content.add_heading("Grid Convergence Studies", level=2)
    
    report.content.add_heading("Free Stream Velocity", level=3)
    
    report.content.add_text(
        "This section presents the convergence study for the free stream "
        "velocity ($U_\\infty$). For the final case, with grid resolution of "
        f"{case.dx}m, an asymptotic ratio of "
        f"{u_infty_convergence[0].asymptotic_ratio:.4g} was achieved "
        "(asymptotic range is indicated by a value $\\approx 1$). The free "
        f"stream velocity at zero grid resolution is {u_infty_exact:.4g}m/s. "
        "The grid resolution required for a fine-grid GCI of "
        f"{gci_required * 100}\% is {u_infty_gci:.4g}m.")
    
    caption = ("Free stream velocity ($U_\\infty$) per grid resolution "
               "with computational cells and error against value at zero grid "
               "resolution")
    report.content.add_table(u_infty_df,
                             index=False,
                             caption=caption)
    
    fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
    u_infty_df.plot(ax=ax, x="# cells", y="error", marker='x')
    plt.yscale("log")
    plt.xscale("log")
    
    plot_name = "u_infty_convergence.png"
    plot_path = report_dir / plot_name
    fig.savefig(plot_path, bbox_inches='tight')
    
    # Add figure with caption
    caption = ("Free stream velocity error against value at zero grid "
               "resolution per grid resolution ")
    report.content.add_image(plot_name, caption, width="3.64in")
    
    report.content.add_heading("Wake Velocity", level=3)
    
    report.content.add_text(
        "This section presents the convergence study for the wake centerline "
        "velocity measured 1.2 diameters downstream from the turbine "
        "($U_{1.2D}$). For the final case, with grid resolution of "
        f"{case.dx}m, an asymptotic ratio of "
        f"{u_wake_convergence[0].asymptotic_ratio:.4g} was achieved "
        "(asymptotic range is indicated by a value $\\approx 1$). The free "
        f"stream velocity at zero grid resolution is {u_wake_exact:.4g}m/s. "
        "The grid resolution required for a fine-grid GCI of "
        f"{gci_required * 100}\% is {u_wake_gci:.4g}m.")
    
    caption = ("Wake centerline velocity 1.2 diameters downstream "
               "($U_{1.2D}$) per grid resolution with computational cells and "
               "error against value at zero grid resolution")
    report.content.add_table(u_wake_df,
                             index=False,
                             caption=caption)
    
    fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
    u_wake_df.plot(ax=ax, x="# cells", y="error", marker='x')
    plt.yscale("log")
    plt.xscale("log")
    
    plot_name = "u_wake_convergence.png"
    plot_path = report_dir / plot_name
    fig.savefig(plot_path, bbox_inches='tight')
    
    # Add figure with caption
    caption = ("Wake velocity error against value at zero grid resolution "
               "per grid resolution")
    report.content.add_image(plot_name, caption, width="3.64in")
    
    report.content.add_heading("Turbulence Intensity", level=3)
    
    report.content.add_text(
        "This section presents the convergence study for the wake centerline "
        "turbulence intensity (TI) measured 1.2 diameters downstream from the "
        "turbine ($k_{1.2D}$). For the final case, with grid resolution of "
        f"{case.dx}m, an asymptotic ratio of "
        f"{ti_wake_convergence[0].asymptotic_ratio:.4g} was achieved "
        "(asymptotic range is indicated by a value $\\approx 1$). TI "
        f"at zero grid resolution is {ti_wake_exact:.4g}\%. "
        "The grid resolution required for a fine-grid GCI of "
        f"{gci_required * 100}\% is {ti_wake_gci:.4g}m.")
    
    caption = ("Wake centerline TI 1.2 diameters downstream "
               "($k_{1.2D}$) per grid resolution with computational cells and "
               "error against value at zero grid resolution")
    report.content.add_table(ti_wake_df,
                             index=False,
                             caption=caption)
    
    fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
    ti_wake_df.plot(ax=ax, x="# cells", y="error", marker='x')
    plt.yscale("log")
    plt.xscale("log")
    
    plot_name = "ti_wake_convergence.png"
    plot_path = report_dir / plot_name
    fig.savefig(plot_path, bbox_inches='tight')
    
    # Add figure with caption
    caption = ("Wake TI error against value at zero grid resolution "
               "per grid resolution")
    report.content.add_image(plot_name, caption, width="3.64in")
    
    report.content.add_heading("Validation", level=3)
    
    report.content.add_text(
        "At zero grid resolution, the normalised deficit of $U_{1.2D}$, "
        f"($\\gamma_{{0(1.2D)}}$) is {gamma0_sim:.4g}\%, a "
        f"{gamma0_err * 100:.4g}\% error against the measured value of "
        f"{gamma0_true:.4g}\%.")
    
    report.content.add_heading("Wake Transects", level=2)
    
    report.content.add_text(
        "This section presents axial velocity transects along the turbine "
        "centreline and at cross-sections along the $y$-axis. Errors are "
        "reported relative to the experimental data given in [@mycek2014].")
    
    for i, transect in enumerate(global_validate):
        
        if transect.name not in ["$u$", "$u_0$"]: continue
        
        description = transect.attrs['description']
        report.content.add_heading(description, level=3)
        
        transect_df = transect_grouped.get_group(description).drop("Transect",
                                                                   axis=1)
        transect_rmse = transect_df.iloc[-1, 1]
        
        report.content.add_text(
            "The root mean square error (RMSE) for this transect at the "
            f"finest grid resolution of {case.dx}m was {transect_rmse:.4g}.")
        
        caption = ("Root mean square error (RMSE) for the normalised "
                   "velocity, $u^*_0$, per grid resolution.")
        report.content.add_table(transect_df,
                                 index=False,
                                 caption=caption)
        
        transect_true = transect.to_xarray()
        major_axis = f"${transect.attrs['major_axis']}^*$"
        
        transect_true_u0 = get_u0(transect_true, transect_true, 0.8)
        transect_true_u0.plot(ax=ustar_axs[i],
                              x=major_axis,
                              label='Experiment')
        
        ustar_axs[i].legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ustar_axs[i].grid()
        ustar_axs[i].set_title("")
        
        plot_name = f"transect_u0_{i}.png"
        plot_path = report_dir / plot_name
        ustar_figs[i].savefig(plot_path, bbox_inches='tight')
        
        # Add figure with caption
        caption = ("Normalised velocity, $u^*_0$, (m/s) per grid resolution "
                   "comparison. Experimental data reverse engineered from "
                   f"[@mycek2014, fig. {transect.attrs['figure']}].")
        report.content.add_image(plot_name, caption, width="5.68in")
        
        transect_true_gamma0 = get_gamma0(transect_true,
                                          transect_true)
        transect_true_gamma0.plot(ax=gamma_axs[i],
                                  x=major_axis,
                                  label='Experiment')
        
        gamma_axs[i].legend(loc='center left', bbox_to_anchor=(1, 0.5))
        gamma_axs[i].grid()
        gamma_axs[i].set_title("")
        
        plot_name = f"transect_gamma0_{i}.png"
        plot_path = report_dir / plot_name
        gamma_figs[i].savefig(plot_path, bbox_inches='tight')
        
        # Add figure with caption
        caption = ("Normalised velocity deficit, $\gamma_0$, (%) per grid "
                   "resolution comparison. Experimental data reverse "
                   "engineered from [@mycek2014, fig. "
                   f"{transect.attrs['figure']}].")
        report.content.add_image(plot_name, caption, width="5.68in")
    
    # Add section for the references
    report.content.add_heading("References", level=2)
    
    # Add report metadata
    os_name = platform.system()
    report.title = f"Grid Convergence Study ({os_name})"
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
                                          '--bibliography=examples.bib',
                                          '--reference-doc=reference.docx'],
                              sandbox=False)
    
    except ImportError:
        
        print(report)


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


def find_project_dir(path, case):
    
    path = Path(path)
    files = list(Path(path).glob("**/case.yaml"))
    ignore_fields = ["stats_interval",
                     "restart_interval"]
    
    for file in files:
        test = MycekStudy.from_yaml(file)
        if test.is_equal(case, ignore_fields):
            return file.parent
    
    return None


def get_unique_dir(path, max_tries=1e6):
    
    parent = Path(path)
    
    for _ in range(int(max_tries)):
        name = uuid.uuid4().hex
        child = parent / name
        if not child.exists(): return child
    
    raise RuntimeError("Could not find unique directory name")


def get_TI(ds):
    velmag = np.sqrt(ds["$u$"]**2 + ds["$v$"]**2 + ds["$w$"]**2)
    return (100 / velmag) * np.sqrt(2 * ds["$k$"] / 3)


def get_u0(da, transect, factor, case=None):
    
    if case is not None:
        da = get_reset_origin(da, (case.turb_pos_x,
                                   case.turb_pos_y,
                                   case.turb_pos_z))
    
    da = get_normalised_dims(da, transect.attrs["$D$"])
    da = get_normalised_data(da, factor)
    
    return da


def get_gamma0(da, transect, case=None):
    
    if case is not None:
        da = get_reset_origin(da, (case.turb_pos_x,
                                   case.turb_pos_y,
                                   case.turb_pos_z))
    
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
        
        if transect.name not in ["$u$", "$u_0$"]: continue
        
        transect_true = transect.to_xarray()
        
        # Compare transect
        transect_sim = result.faces.extract_z(-1, **transect)
        
        # Determine plot x-axis
        major_axis = f"${transect.attrs['major_axis']}^*$"
        
        # Create and save a u0 figure
        transect_sim_u0 = get_u0(transect_sim["$u$"],
                                 transect_true,
                                 factor,
                                 case)
        
        transect_sim_u0.plot(ax=ustar_ax[i],
                             x=major_axis,
                             label=f'{case.dx}m')
        
        # Create and save a gamma0 figure
        transect_sim_gamma0 = get_gamma0(transect_sim["$u$"],
                                         transect_true,
                                         case)
        
        transect_sim_gamma0.plot(ax=gamma_ax[i],
                                 x=major_axis,
                                 label=f'{case.dx}m')


def get_rmse(estimated, observed):
    estimated = estimated[~np.isnan(estimated)]
    if len(estimated) == 0: return np.nan
    observed = observed[:len(estimated)]
    return np.sqrt(((estimated - observed[:len(estimated)]) ** 2).mean())


def get_transect_error(case, validate, result, factor, data):
    
    for i, transect in enumerate(validate):
        
        if transect.name not in ["$u$", "$u_0$"]: continue
        
        transect_true = transect.to_xarray()
        
        # Compare transect
        transect_sim = result.faces.extract_z(-1, **transect)
        
        transect_sim_u0 = get_u0(transect_sim["$u$"],
                                 transect_true,
                                 factor,
                                 case)
        
        transect_true_u0 = get_u0(transect_true,
                                  transect_true,
                                  transect_true.attrs["$U_\infty$"],
                                  case)
        
        # Calculate RMS error and store
        rmse = get_rmse(transect_sim_u0.values, transect_true_u0.values)
        data["resolution (m)"].append(case.dx)
        data["Transect"].append(transect.attrs['description'])
        data["RMSE"].append(rmse)


def get_cells(case):
    top = (case.x1 - case.x0) * (case.y1 - case.y0) * case.sigma
    bottom = case.dx * case.dy
    return top / bottom


def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        msg = f"{value} is an invalid positive int value"
        raise argparse.ArgumentTypeError(msg)
    return ivalue


if __name__ == "__main__":
    
    import argparse
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='MODEL',
                                       required=True)
    
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--experiments',
                               type=check_positive,
                               choices=range(3, 6),
                               default=5,
                               help=("number of experiments to run - defaults "
                                     "to 5"))
    
    parser_fm = subparsers.add_parser('fm',
                                      parents=[parent_parser],
                                      help='execute flexible mesh model')
    parser_fm.add_argument('--threads',
                           type=check_positive,
                           default=1,
                           help=("number of CPU threads to utilise - defaults "
                                 "to 1"))
    
    parser_structured = subparsers.add_parser('structured',
                                              parents=[parent_parser],
                                              help='execute structured model')
    
    args = parser.parse_args()
    
    if "threads" not in args:
        args.threads = 1
    
    main(args.MODEL, args.experiments, args.threads)
