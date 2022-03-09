# -*- coding: utf-8 -*-

import os
import shutil
import platform
from pathlib import Path
from dataclasses import replace

import matplotlib
import matplotlib.pyplot as plt

from snl_d3d_cec_verify import (MycekStudy,
                                Report,
                                Result,
                                LiveRunner,
                                Template)
from snl_d3d_cec_verify.result import get_normalised_data
from snl_d3d_cec_verify.text import Spinner

matplotlib.rcParams.update({'font.size': 8})


def main(grid_resolution, omp_num_threads):
    
    # Set reporting times
    sigma = int(2 / grid_resolution)
    
    kwargs = {"dx": grid_resolution,
              "dy": grid_resolution,
              "sigma": sigma,
              "restart_interval": 600}
    
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
        
        run_directory = Path("comparison_runs") / template_type
        run_directory.mkdir(exist_ok=True, parents=True)
        
        # Run without turbines
        no_turb_case = replace(cases[template_type], simulate_turbines=False)
        no_turb_dir = run_directory / "no_turbine"
        
        if no_turb_dir.is_dir():
            try:
                Result(no_turb_dir)
            except FileNotFoundError:
                shutil.rmtree(no_turb_dir)
        
        if no_turb_dir.is_dir():
            try:
                Result(no_turb_dir)
            except FileNotFoundError:
                shutil.rmtree(no_turb_dir)
        
        # Determine $U_\infty$ for case, by running without the turbine
        if not no_turb_dir.is_dir():
            
            if d3d_bin_path is None:
                d3d_bin_path = get_env(bin_var)
                print(f'Setting {template_type} bin folder path to '
                      f'{d3d_bin_path}')
            
            print(f"Simulating {template_type} model without turbine")
            
            # Use the LiveRunner class to get real time feedback from the 
            # Delft3D calculation
            runner = LiveRunner(d3d_bin_path,
                                omp_num_threads=omp_num_threads)
            
            no_turb_dir.mkdir()
            template(no_turb_case, no_turb_dir)
            
            with Spinner() as spin:
                for line in runner(no_turb_dir):
                    spin(line)
        
        result = Result(no_turb_dir)
        u_infty_ds = result.faces.extract_turbine_centre(-1, no_turb_case)
        u_infty[template_type] = u_infty_ds["$u$"].values.take(0)
        
        # Run with turbines
        turb_dir = run_directory / "turbine"
        
        if turb_dir.is_dir():
            try:
                Result(turb_dir)
            except FileNotFoundError:
                shutil.rmtree(turb_dir)
        
        if not turb_dir.is_dir():
            
            if d3d_bin_path is None:
                d3d_bin_path = get_env(bin_var)
                print(f'Setting {template_type} bin folder path to '
                      f'{d3d_bin_path}')
            
            print(f"Simulating {template_type} model with turbine")
            
            # Use the LiveRunner class to get real time feedback from the 
            # Delft3D calculation
            runner = LiveRunner(d3d_bin_path,
                                omp_num_threads=omp_num_threads)
            
            turb_dir.mkdir()
            template(cases[template_type], turb_dir)
            
            with Spinner() as spin:
                for line in runner(turb_dir):
                    spin(line)
        
        results[template_type] = Result(turb_dir)
    
    print("Post processing...")
    
    section = "Axial Velocity Comparison"
    report.content.add_heading(section)
    
    for template_type in template_types:
        
        case = cases[template_type]
        result = results[template_type]
        turb_z = result.faces.extract_turbine_z(-1, case)
        unorm = get_normalised_data(turb_z["$u$"], u_infty[template_type])
        
        fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
        unorm.plot(x="$x$", y="$y$")
        
        plot_name = f"turb_z_u_{template_type}.png"
        plot_path = report_dir / plot_name
        fig.savefig(plot_path, bbox_inches='tight')
        
        # Add figure with caption
        caption = f"Axial velocity (m/s) for the {template_type} model type"
        report.content.add_image(plot_name, caption, width="3.64in")
    
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
                              extra_args=['-C',
                                          f'--resource-path={report_dir}',
                                          '--reference-doc=reference.docx'])
    
    except ImportError:
        
        print(report)


def get_env(variable):
    
    env = dict(os.environ)
    
    if variable in env:
        root = Path(env[variable].replace('"', ''))
        print(f'{variable} found')
    else:
        raise ValueError(f'{variable} not found')
    
    return root.resolve()


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
                        default=0.25,
                        help=("grid resolution - defaults to 0.25"))
    
    parser.add_argument('--threads',
                        type=check_positive,
                        default=1,
                        help=("number of CPU threads to utilise for the fm "
                              "model- defaults to 1"))
    
    args = parser.parse_args()
    main(args.grid_resolution, args.threads)
