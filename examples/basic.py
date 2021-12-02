# -*- coding: utf-8 -*-

import os
import tempfile
from pathlib import Path
from collections import defaultdict

import pandas as pd
import matplotlib.pyplot as plt

from snl_d3d_cec_verify import CaseStudy, Report, Result, Runner, Template

env = dict(os.environ)
d3d_bin_path = Path(env['D3D_BIN'].replace('"', ''))
template = Template()
runner = Runner(d3d_bin_path)
report = Report(79, "%d %B %Y")
report_dir = Path("basic_report")
report_dir.mkdir(exist_ok=True)
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
        turb_u = turb_ds.u.values.take(0)
        
        # Record data for table
        data["discharge"].append(case.discharge)
        data["u"].append(turb_u)
        
        # Add report section with plot
        report.content.add_heading(
            f"Discharge: {case.discharge} (cubic meters per second)",
            level=2)
        
        fig, ax = plt.subplots()
        turbz = result.faces.extract_turbine_z(-1, case)
        turbz["u"].plot(ax=ax, x="x", y="y")
        plot_name = f"discharge_case_{i}.png"
        plot_path = report_dir / plot_name
        plt.savefig(plot_path)
        
        report.content.add_image(plot_name, "u-velocity (m/s)")

df = pd.DataFrame(data)
report.content.add_heading("Results", level=2)
report.content.add_table(df,
                         index=False,
                         caption="Turbine centre velocity per discharge level")

report.title = "Basic Example"
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
                                      '--reference-doc=reference.docx'])

except ImportError:
    
    print(report)
