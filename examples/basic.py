# -*- coding: utf-8 -*-

import os
import platform
import tempfile
from pathlib import Path
from collections import defaultdict

import pandas as pd
import matplotlib.pyplot as plt

from snl_d3d_cec_verify import CaseStudy, Report, Result, Runner, Template

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


def main(template_type):
    
    template = Template(template_type)
    runner = Runner(get_d3d_bin_path())
    report = Report(79, "%d %B %Y")
    report_dir = Path(template_type) / "basic_report"
    report_dir.mkdir(exist_ok=True, parents=True)
    data = defaultdict(list)
    
    cases = CaseStudy(discharge=[4, 5, 6, 7, 8])
    
    for i, case in enumerate(cases):
    
        with tempfile.TemporaryDirectory() as tmpdirname:
            
            # Create the project and then run it
            template(case, tmpdirname)
            runner(tmpdirname)
            
            # Pick up the results
            result = Result(tmpdirname)
            turb_ds = result.faces.extract_turbine_centre(-1, case)
            turb_u = turb_ds["$u$"].values.take(0)
            turb_k = turb_ds["$k$"].values.take(0)
            
            # Record data for table
            data["discharge"].append(case.discharge)
            data["u"].append(turb_u)
            data["k"].append(turb_k)
            
            # Add report section with plot
            report.content.add_heading(
                f"Discharge: {case.discharge} (cubic meters per second)",
                level=2)
            
            turbz = result.faces.extract_turbine_z(-1, case)
            
            fig, ax = plt.subplots()
            turbz["$u$"].plot(ax=ax, x="$x$", y="$y$")
            plot_name = f"discharge_case_{i}_u.png"
            plot_path = report_dir / plot_name
            plt.savefig(plot_path)
            
            report.content.add_image(plot_name, 
                                     "Velocity, $u$ (m/s)",
                                     width="4in")
            
            fig, ax = plt.subplots()
            turbz["$k$"].plot(ax=ax, x="$x$", y="$y$")
            plot_name = f"discharge_case_{i}_k.png"
            plot_path = report_dir / plot_name
            plt.savefig(plot_path)
            
            report.content.add_image(plot_name,
                                     "Turbulent kinetic energy, $k$ "
                                     "(m^2^/s^2^)",
                                     width="4in")
    
    df = pd.DataFrame(data)
    
    report.content.add_heading("Results", level=2)
    
    report.content.add_table(df,
                             index=False,
                             caption="Turbine centre velocity and TKE per "
                                     "discharge level")
    
    os_name = platform.system()
    report.title = f"Basic Example ({os_name})"
    report.date = "today"
    
    with open(report_dir / "report.md", "wt") as f:
        for line in report:
            f.write(line)
    
    try:
        
        import pypandoc
        
        pypandoc.convert_file(f"{report_dir / 'report.md'}",
                              'docx',
                              outputfile=f"{report_dir / 'report.docx'}",
                              extra_args=[f'--resource-path={report_dir}',
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
