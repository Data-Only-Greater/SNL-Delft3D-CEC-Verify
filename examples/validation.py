# -*- coding: utf-8 -*-

import os
import platform
import tempfile
from pathlib import Path
from collections import defaultdict

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


def get_normalised(da, case, transect):
    
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


def get_TI(ds):
    velmag = np.sqrt(ds["$u$"]**2 + ds["$v$"]**2 + ds["$w$"]**2)
    return (100 / velmag) * np.sqrt(2 * ds["$k$"] / 3)


def get_rmse(estimated, observed):
    return np.sqrt(((estimated - observed) ** 2).mean())


def main(template_type):
    
    case = MycekStudy()
    template = Template(template_type)
    runner = Runner(get_d3d_bin_path())
    report = Report(79, "%d %B %Y")
    validate = Validate(case)
    
    report_dir = Path(template_type) / "validation_report"
    report_dir.mkdir(exist_ok=True, parents=True)
    
    data_u0 = defaultdict(list)
    data_I0 = defaultdict(list)
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        
        # Create the project and then run it
        template(case, tmpdirname)
        runner(tmpdirname)
        
        # Pick up the results
        result = Result(tmpdirname)
        
        for i, transect in enumerate(validate):
            
            if transect.name not in ["$u$", "$u_0$"]: continue
            
            # Compare transect
            transect_sim = result.faces.extract_z(-1, **transect)
            transect_true = transect.to_xarray()
            
            # Add report section with plot
            report.content.add_heading(transect.attrs['description'],
                                       level=2)
            
            # Determine plot x-axis
            major_axis = f"${transect.attrs['major_axis']}^*$"
            
            # Create and save a u0 figure
            transect_sim_u0 = get_normalised(transect_sim["$u$"],
                                             case,
                                             transect_true)
            transect_true_u0 = get_normalised(transect_true,
                                              case,
                                              transect_true)
            
            fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
            transect_sim_u0.plot(ax=ax, x=major_axis, label='Delft3D')
            transect_true_u0.plot(ax=ax, x=major_axis, label='Experiment')
            ax.legend()
            ax.grid()
            ax.set_title("")
            
            plot_name = f"transect_u0_{i}.png"
            plot_path = report_dir / plot_name
            plt.savefig(plot_path, bbox_inches='tight')
            
            # Add figure with caption
            caption = ("$u_0$ comparison (m/s). Experimental data reverse "
                       "engineered  from [@mycek2014, fig. "
                       f"{transect.attrs['figure']}].")
            report.content.add_image(plot_name, caption, width="4in")
            
            # Calculate RMS error and store
            rmse = get_rmse(transect_sim_u0.values, transect_true_u0.values)
            data_u0["Transect"].append(transect.attrs['description'])
            data_u0["RMSE (m/s)"].append(rmse)
            
            # Create and save a gamma0 figure
            transect_sim_gamma0 = get_gamma0(transect_sim["$u$"],
                                             case,
                                             transect_true)
            transect_true_gamma0 = get_gamma0(transect_true,
                                              case,
                                              transect_true)
            
            fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
            transect_sim_gamma0.plot(ax=ax, x=major_axis, label='Delft3D')
            transect_true_gamma0.plot(ax=ax, x=major_axis, label='Experiment')
            ax.legend()
            ax.grid()
            ax.set_title("")
            
            plot_name = f"transect_gammm0_{i}.png"
            plot_path = report_dir / plot_name
            plt.savefig(plot_path, bbox_inches='tight')
            
            # Add figure with caption
            caption = ("$\gamma_0$ comparison (%). Experimental data reverse "
                       "engineered from [@mycek2014, fig. "
                       f"{transect.attrs['figure']}].")
            report.content.add_image(plot_name, caption, width="4in")
        
        for i, transect in enumerate(validate):
            
            if transect.name != "$I_0$": continue
            
            # Compare transect
            transect_sim = result.faces.extract_z(-1, **transect)
            transect_sim = transect_sim.assign({"$I$": get_TI})
            transect_true = transect.to_xarray()
            
            # Add report section with plot
            report.content.add_heading(transect.attrs['description'],
                                       level=2)
            
            # Determine plot x-axis
            major_axis = f"${transect.attrs['major_axis']}^*$"
            
            # Create and save a u0 figure
            transect_sim_I0 = get_normalised(transect_sim["$I$"],
                                             case,
                                             transect_true)
            transect_true_I0 = get_normalised(transect_true,
                                              case,
                                              transect_true)
            
            fig, ax = plt.subplots(figsize=(4, 2.75), dpi=300)
            transect_sim_I0.plot(ax=ax, x=major_axis, label='Delft3D')
            transect_true_I0.plot(ax=ax, x=major_axis, label='Experiment')
            ax.legend()
            ax.grid()
            ax.set_title("")
            
            plot_name = f"transect_I0_{i}.png"
            plot_path = report_dir / plot_name
            plt.savefig(plot_path, bbox_inches='tight')
            
            # Add figure with caption
            caption = ("$I_0$ comparison (%). Experimental data "
                       "reverse engineered  from [@mycek2014, fig. "
                       f"{transect.attrs['figure']}].")
            report.content.add_image(plot_name, caption, width="4in")
            
            # Calculate RMS error and store
            rmse = get_rmse(transect_sim_I0.values, transect_true_I0.values)
            data_I0["Transect"].append(transect.attrs['description'])
            data_I0["RMSE (%)"].append(rmse)
    
    # Add tables for errors
    report.content.add_heading("Errors", level=2)
    
    df = pd.DataFrame(data_u0)
    caption = "Root-mean-square errors in $u_0$."
    report.content.add_table(df,
                             index=False,
                             caption=caption)
    
    df = pd.DataFrame(data_I0)
    caption = "Root-mean-square errors in $I_0$."
    report.content.add_table(df,
                             index=False,
                             caption=caption)
    
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
                                          '--bibliography=examples.bib',
                                          '--reference-doc=reference.docx'],
                              sandbox=False)
    
    except ImportError:
        
        print(report)


if __name__ == "__main__":
    
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('MODEL',
                        choices=['fm', 'structured'],
                        help=("the type of model to be exectuted - choose "
                              "'fm' or 'structured'"))
    
    args = parser.parse_args()
    main(args.MODEL)
