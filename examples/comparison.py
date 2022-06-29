# -*- coding: utf-8 -*-

import os
import uuid
import platform
from pathlib import Path
from dataclasses import replace

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from snl_d3d_cec_verify import (MycekStudy,
                                Report,
                                Result,
                                LiveRunner,
                                Template,
                                Validate)
from snl_d3d_cec_verify.result import get_normalised_data
from snl_d3d_cec_verify.text import Spinner

matplotlib.rcParams.update({'font.size': 8})


def main(grid_resolution, omp_num_threads):
    
    # Set reporting times
    sigma = int(2 / grid_resolution)
    
    report = Report(79, "%d %B %Y")
    report_dir = Path("comparison_report")
    report_dir.mkdir(exist_ok=True, parents=True)
    
    cases = {}
    u_infty = {}
    results = {}
    
    template_types = ["fm", "structured"]
    
    # Run stage
    for template_type in template_types:
        
        d3d_bin_path = None
        kwargs = {"dx": grid_resolution,
                  "dy": grid_resolution,
                  "sigma": sigma,
                  "restart_interval": 600}
        
        # Choose options based on the template type
        if template_type == "fm":
            
            bin_var = 'D3D_FM_BIN'
            kwargs["stats_interval"] = 240 / (sigma ** 2)
        
        elif template_type == "structured":
            
            bin_var = 'D3D_4_BIN'
            
            # Set time step based on flexible mesh runs
            dt_init_map = {1.0: 0.5,
                           0.5: 0.25,
                           0.25: 0.1,
                           0.125: 0.0375,
                           0.0625: 0.0125}
            
            if grid_resolution not in dt_init_map:
                raise ValueError(f"Grid resolution '{grid_resolution}' "
                                  "not valid.")
            
            kwargs["dt_init"] = dt_init_map[grid_resolution]
        
        cases[template_type] = MycekStudy(**kwargs)
        template = Template(template_type)
        
        run_directory = Path(template_type) / "runs"
        run_directory.mkdir(exist_ok=True, parents=True)
        
        # Run without turbines
        no_turb_case = replace(cases[template_type], simulate_turbines=False)
        no_turb_dir = find_project_dir(run_directory, no_turb_case)
        result = None
        
        if no_turb_dir is not None:
            try:
                print("Loading pre-existing simulation at path "
                      f"'{no_turb_dir}'")
                result = Result(no_turb_dir)
            except FileNotFoundError:
                pass
        
        if result is None:
            
            no_turb_dir = get_unique_dir(run_directory)
            
            if d3d_bin_path is None:
                print(f'Setting {template_type} bin folder path to '
                      f'{d3d_bin_path}')
                d3d_bin_path = get_env(bin_var)
            
            print(f"Simulating {template_type} model without turbine")
            
            # Use the LiveRunner class to get real time feedback from the 
            # Delft3D calculation
            runner = LiveRunner(d3d_bin_path,
                                omp_num_threads=omp_num_threads)
            
            # Make template and record case
            no_turb_dir.mkdir()
            template(no_turb_case, no_turb_dir)
            case_path = no_turb_dir / "case.yaml"
            no_turb_case.to_yaml(case_path)
            
            with Spinner() as spin:
                for line in runner(no_turb_dir):
                    spin(line)
        
            result = Result(no_turb_dir)
        
        u_infty_ds = result.faces.extract_turbine_centre(-1, no_turb_case)
        u_infty[template_type] = u_infty_ds["$u$"].values.take(0)
        
        # Run with turbines
        turb_case = cases[template_type]
        turb_dir = find_project_dir(run_directory, turb_case)
        result = None
        
        if turb_dir is not None:
            try:
                print(f"Loading pre-existing simulation at path '{turb_dir}'")
                result = Result(turb_dir)
            except FileNotFoundError:
                pass
        
        if result is None:
            
            turb_dir = get_unique_dir(run_directory)
            
            if d3d_bin_path is None:
                print(f'Setting {template_type} bin folder path to '
                      f'{d3d_bin_path}')
                d3d_bin_path = get_env(bin_var)
            
            print(f"Simulating {template_type} model with turbine")
            
            # Use the LiveRunner class to get real time feedback from the 
            # Delft3D calculation
            runner = LiveRunner(d3d_bin_path,
                                omp_num_threads=omp_num_threads)
            
            # Make template and record case
            turb_dir.mkdir()
            template(turb_case, turb_dir)
            case_path = turb_dir / "case.yaml"
            turb_case.to_yaml(case_path)
            
            with Spinner() as spin:
                for line in runner(turb_dir):
                    spin(line)
            
            result = Result(turb_dir)
        
        results[template_type] = result
    
    print("Post processing...")
    
    section = "Introduction"
    report.content.add_heading(section)
    
    text = ("This is a comparison of the performance of simulations of the "
            "Mycek flume experiment [@mycek2014]  using the flexible mesh "
            "(FM) and structured grid solvers for Delft3D. The simulation "
            "settings are mirrored between the two methods as much as "
            "possible. The chosen grid resolution for this study is "
            f"{grid_resolution}m. Axial and radial velocities in the "
            "horizontal plane intersecting the turbine hub will be examined.")
    report.content.add_text(text)
    
    section = "Axial Velocity Comparison"
    report.content.add_heading(section, label="sec:axial")
    
    validate = Validate(turb_case)
    turb_zs = {}
    unorms = {}
    maxus = []
    
    plot_names = []
    captions = []
    fig_labels = []
    
    for template_type in template_types:
        
        case = cases[template_type]
        result = results[template_type]
        turb_z = result.faces.extract_turbine_z(-1, case)
        unorm = get_normalised_data(turb_z["$u$"], u_infty[template_type])
        
        turb_zs[template_type] = turb_z
        unorms[template_type] = unorm
        
        fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
        unorm.plot(x="$x$", y="$y$", vmin=0.55, vmax=1.05)
        
        plot_name = f"turb_z_u_{template_type}"
        plot_file_name = f"{plot_name}.png"
        plot_names.append(plot_file_name)
        plot_path = report_dir / plot_name
        fig.savefig(plot_path, bbox_inches='tight')
        
        # Add figure caption
        caption = ("Axial velocity normalised by the free stream velocity "
                   f"for the {template_type} model type")
        captions.append(caption)
        
        fig_label = f"fig:{plot_name}"
        fig_labels.append(fig_label)
        
        # Collect maximimum u*
        maxus.append(unorm.max())
    
    label_text = "; ".join([f"@{x.capitalize()}" for x in fig_labels])
    label_text = f"[{label_text}]"
    text = ("This section compares axial velocities between the FM and "
            f"structured grid models. {label_text} show the axial velocity "
            "over the horizontal plane intersecting the turbine hub for the "
            "FM and structured gird models, respectively. The "
            "units are non-dimensionalised by the free-stream velocity, "
            "measured at the hub location without the presence of the "
            "turbine. If $u$ is the dimensional velocity, and $u_\infty$ is "
            "the dimensional free stream velocity, then the normalized "
            "velocity $u^* =  u / u_\infty$. Note the observable difference "
            "in the wake velocities immediately downstream of the turbine "
            "between the two simulations.")
    report.content.add_text(text)
    
    for plot_name, caption, fig_label in zip(plot_names, captions, fig_labels):
        report.content.add_image(plot_name,
                                 caption,
                                 label=fig_label,
                                 width="3.64in")
    
    # Plot the relative error
    maxu = max(maxus)
    diffu = (unorms["structured"] - unorms["fm"]) / maxu
    maxdiffu = np.fabs(diffu.values).max()
    
    fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
    diffu.plot(ax=ax,
               x="$x$",
               y="$y$",
               cbar_kwargs={"label": "$u* / u*_{\\mathrm{max}}$"})
    
    circle_rad = 6
    ax.plot(6.1, 3.46, 'o',
            ms=circle_rad * 2, mec='k', mfc='none', mew=1)
    ax.annotate('Acceleration', xy=(6, 3.4), xytext=(30, 30),
                textcoords='offset points', color='k',
                arrowprops=dict(arrowstyle=('simple,'
                                            'head_width=0.7,'
                                            'head_length=0.8,'
                                            'tail_width=0.1'),
                                lw=0.2,
                                facecolor='k',
                                shrinkB=circle_rad * 2))
    
    ax.annotate('Near wake', xy=(7, 3), xytext=(-20, -60),
                textcoords='offset points', color='k',
                arrowprops=dict(arrowstyle=('simple,'
                                            'head_width=0.7,'
                                            'head_length=0.8,'
                                            'tail_width=0.1'),
                                lw=0.2,
                                facecolor='k'))
    
    ax.annotate('Far wake', xy=(15, 3), xytext=(-20, -60),
                textcoords='offset points', color='k',
                arrowprops=dict(arrowstyle=('simple,'
                                            'head_width=0.7,'
                                            'head_length=0.8,'
                                            'tail_width=0.1'),
                                lw=0.2,
                                facecolor='k'))
    
    plot_name = "turb_z_u_diff"
    plot_file_name = f"{plot_name}.png"
    plot_path = report_dir / plot_file_name
    fig.savefig(plot_path, bbox_inches='tight')
    fig_label_diffu = f"fig:{plot_name}"
    
    text = (f"[@{fig_label_diffu.capitalize()}] shows the error between the "
            "non-dimensional axial velocities of the structured grid and FM "
            "models, relative to the maximum value within the two "
            "simulations. Three main areas of difference are revealed, the "
            "increased deficit in the near wake for the structured model, the "
            "reduced deficit of the structured model in the far wake and the "
            "increased acceleration around the edges of the turbine of the "
            "structured model.")
    report.content.add_text(text)
    
    # Add figure with caption
    caption = ("Relative error in normalised axial velocity between the "
               "structured and fm models")
    report.content.add_image(plot_file_name,
                             caption,
                             label=fig_label_diffu,
                             width="3.64in")
    
    # Centerline velocity
    transect3 = validate[0]
    transect15 = validate[1]
    
    transect_fm = results["fm"].faces.extract_z(-1, **transect3)
    transect_structured = results["structured"].faces.extract_z(-1,
                                                                **transect3)
    transect3_true = transect3.to_xarray()
    transect15_true = transect15.to_xarray()
    
    transect_fm_unorm = get_normalised_data(transect_fm["$u$"], u_infty["fm"])
    transect_structured_unorm = get_normalised_data(transect_structured["$u$"],
                                                    u_infty["structured"])
    transect3_true_unorm = get_normalised_data(transect3_true, 0.8)
    transect15_true_unorm = get_normalised_data(transect15_true, 0.8)
    
    fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
    transect_fm_unorm.plot(ax=ax, x="$x$", label='fm')
    transect_structured_unorm.plot(ax=ax, x="$x$", label='structured')
    transect3_true_unorm.plot(ax=ax, x="$x$", label='experiment (3% TI)')
    transect15_true_unorm.plot(ax=ax, x="$x$", label='experiment (15% TI)')
    ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
    ax.grid()
    ax.set_title("")
    
    plot_name = "transect_u"
    plot_file_name = f"{plot_name}.png"
    plot_path = report_dir / plot_file_name
    fig.savefig(plot_path, bbox_inches='tight')
    fig_label_transect = f"fig:{plot_name}"
    
    text = ("Comparing the non-dimensional centerline velocities alongside "
            "the experimental data (published in [@mycek2014]) for two "
            "turbulence intensity (TI) levels, in "
            f"[@{fig_label_transect}], confirms the behavior in the near and "
            f"far wake shown in [@{fig_label_diffu}]. Generally, the "
            "structured model performs better in the near wake compared to "
            "the experimental data. In the far wake, the FM model better "
            "repesents the 3% TI experimental data, and the structured model "
            "matches better to the 15\% TI experimental data. "
            "Nonetheless, neither model captures the experimental "
            "measurements well for the whole centerline. Note that the "
            "TI within the Delft3D simulations is between 5\% and 6\%.")
    report.content.add_text(text)
    
    # Add figure with caption
    caption = ("Comparison of the normalised turbine centerline velocity. "
               "Experimental data reverse engineered from [@mycek2014, figs. "
               f"{transect3.attrs['figure']} \& "
               f"{transect15.attrs['figure']}].")
    report.content.add_image(plot_file_name,
                             caption,
                             label=fig_label_transect,
                             width="5.5in")
    
    # Radial velocity
    section = "Radial Velocity Comparison"
    report.content.add_heading(section, label="sec:radial")
    
    vnorms = {}
    maxvs = []
    
    plot_names = []
    captions = []
    fig_labels = []
    
    for template_type in template_types:
        
        turb_z = turb_zs[template_type]
        vnorm = get_normalised_data(turb_z["$v$"], u_infty[template_type])
        vnorms[template_type] = vnorm
        
        fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
        vnorm.plot(x="$x$", y="$y$", vmin=-0.059, vmax=0.059, cmap='RdBu_r')
        
        plot_name = f"turb_z_v_{template_type}"
        plot_file_name = f"{plot_name}.png"
        plot_names.append(plot_file_name)
        plot_path = report_dir / plot_file_name
        fig.savefig(plot_path, bbox_inches='tight')
        
        caption = ("Radial velocity normalised by the free stream velocity "
                   f"for the {template_type} model type")
        captions.append(caption)
        
        fig_label = f"fig:{plot_name}"
        fig_labels.append(fig_label)
        
        # Collect maximimum u*
        maxvs.append(vnorm.max())
    
    label_text = "; ".join([f"@{x.capitalize()}" for x in fig_labels])
    label_text = f"[{label_text}]"
    text = ("This section compares radial velocities between the FM and "
            f"structured grid models. {label_text} show the radial velocity "
            "over the horizontal plane intersecting the turbine hub for the "
            "FM and structured gird models, respectively. The units are "
            "non-dimensionalized by the free-stream velocity, (in the axial "
            "direction) measured at the hub location without the presence of "
            "the turbine. If $v$ is the dimensional velocity, then the "
            "normalized velocity $v^* =  v / u_\infty$. Note the increased "
            "radial velocities recorded for the structured grid compared to "
            "the FM simulation.")
    report.content.add_text(text)
    
    for plot_name, caption, fig_label in zip(plot_names, captions, fig_labels):
        report.content.add_image(plot_name,
                                 caption,
                                 label=fig_label,
                                 width="3.64in")
    
    # Plot the relative error
    maxv = max(maxvs)
    diffv = (vnorms["structured"] - vnorms["fm"]) / maxv
    maxdiffv = np.fabs(diffv.values).max()
    
    fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
    diffv.plot(ax=ax,
               x="$x$",
               y="$y$",
               cbar_kwargs={"label": "$v* / v*_{\\mathrm{max}}$"})
    
    plot_name = "turb_z_v_diff"
    plot_file_name = f"{plot_name}.png"
    plot_path = report_dir / plot_file_name
    fig.savefig(plot_path, bbox_inches='tight')
    fig_label_diffv = f"fig:{plot_name}"
    
    text = (f"[@{fig_label_diffv.capitalize()}] shows the error between the "
            "non-dimensional radial velocities of the structured grid and FM "
            "models, relative to the maximum value within the two "
            "simulations. The largest errors are seen upstream of the "
            "turbine, while smaller errors are seen downstream of the "
            "turbine. The errors in the radial flow are also much higher than "
            "for the axial flow, with the maximum error in radial velocity "
            f"being {maxdiffv:.4g}, while the error is {maxdiffu:.4g} for the "
            f"axial velocity (from [@{fig_label_diffu}]).")
    report.content.add_text(text)
    
    # Add figure with caption
    caption = ("Relative error in normalised radial velocity between the "
               "structured and fm models")
    report.content.add_image(plot_file_name,
                             caption,
                             label=fig_label_diffv,
                             width="3.64in")
    
    # Turbulence intensity
    section = "Turbulence Intensity Comparison"
    report.content.add_heading(section, label="sec:TI")
    
    tis = {}
    
    plot_names = []
    captions = []
    fig_labels = []
    
    for template_type in template_types:
        
        turb_z = turb_zs[template_type]
        ti_turb_z = turb_z.assign({"$I$": get_TI})
        tis[template_type] = ti_turb_z
        
        fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
        ti_turb_z["$I$"].plot(x="$x$", y="$y$", vmin=4, vmax=15)
        
        plot_name = f"turb_z_ti_{template_type}"
        plot_file_name = f"{plot_name}.png"
        plot_names.append(plot_file_name)
        plot_path = report_dir / plot_file_name
        fig.savefig(plot_path, bbox_inches='tight')
        
        caption = (f"Turbulence intensity (\%) for the {template_type} model "
                   "type")
        captions.append(caption)
        
        fig_label = f"fig:{plot_name}"
        fig_labels.append(fig_label)
    
    for plot_name, caption, fig_label in zip(plot_names, captions, fig_labels):
        report.content.add_image(plot_name,
                                 caption,
                                 label=fig_label,
                                 width="3.64in")
    
    # Plot the diff
    diffti = (tis["structured"] - tis["fm"])
    
    fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
    diffti["$I$"].plot(ax=ax, x="$x$", y="$y$")
    
    plot_name = "turb_z_ti_diff"
    plot_file_name = f"{plot_name}.png"
    plot_path = report_dir / plot_file_name
    fig.savefig(plot_path, bbox_inches='tight')
    fig_label_diffti = f"fig:{plot_name}"
    
    # Add figure with caption
    caption = ("Difference in TI between the structured and FM simulations")
    report.content.add_image(plot_file_name,
                             caption,
                             label=fig_label_diffti,
                             width="3.64in")
    
    # Conclusion
    report.content.add_heading("Conclusion")
    
    text = ("Comparison of simulations of the 2014 Mycek flume experiment "
            "[@mycek2014] using the flexible mesh (FM) and structured grid "
            "solvers for Delft3D, reveals significant differences. As "
            "seen in [@sec:axial], differences in the axial velocities "
            "between the two methods were seen in the near wake, far wake, "
            "and at the turbine edges. When comparing to the experimental "
            f"data, as in [@{fig_label_diffu}], it was observed that the "
            "structured grid simulation performs better in the near wake, "
            "while the FM simulation is better in the far wake. In "
            "[@sec:radial], radial velocities were compared with differences "
            "seen immediately upstream and downstream of the turbine (see "
            f"[@{fig_label_diffv}]). Notably, the maximum relative errors "
            "between the two simulations were much larger for the radial "
            f"velocities than then axial velocities, {maxdiffv:.4g} and "
            f"{maxdiffu:.4g} respectively. This discrepancy may account for "
            "some of the differences seen in the axial flows, although the "
            "underlying mechanisms are not yet known. Other factors may also "
            "be contributing, including interpretation of the simulation "
            "parameters or selection of the time step for the structured grid "
            "simulations.")
    report.content.add_text(text)
    
    # Add section for the references
    report.content.add_heading("References", level=2)
    
    # Add report metadata
    os_name = platform.system()
    report.title = f"Model Comparison ({os_name})"
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
                              extra_args=['--filter=pandoc-crossref',
                                          '-C',
                                          '-N',
                                          f'--resource-path={report_dir}',
                                          '--bibliography=examples.bib',
                                          '--reference-doc=reference.docx'],
                              sandbox=False)
    
    except ImportError:
        
        print(report)


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


def get_env(variable):
    
    env = dict(os.environ)
    
    if variable in env:
        root = Path(env[variable].replace('"', ''))
        print(f'{variable} found')
    else:
        raise ValueError(f'{variable} not found')
    
    return root.resolve()


def get_TI(ds):
    velmag = np.sqrt(ds["$u$"]**2 + ds["$v$"]**2 + ds["$w$"]**2)
    return (100 / velmag) * np.sqrt(2 * ds["$k$"] / 3)


def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        msg = f"{value} is an invalid positive int value"
        raise argparse.ArgumentTypeError(msg)
    return ivalue


if __name__ == "__main__":
    
    import argparse
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--grid-resolution',
                        type=float,
                        choices=[1.0, 0.5, 0.25, 0.125, 0.0625],
                        default=0.0625,
                        help=("grid resolution - defaults to 0.0625"))
    
    parser.add_argument('--threads',
                        type=check_positive,
                        default=1,
                        help=("number of CPU threads to utilise for the fm "
                              "model- defaults to 1"))
    
    args = parser.parse_args()
    main(args.grid_resolution, args.threads)
