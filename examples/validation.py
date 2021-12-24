# -*- coding: utf-8 -*-

import os
import tempfile
from pathlib import Path

import pandas as pd
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


def get_gamma0(da, case, transect):
    
    da = get_reset_origin(da,
                          (case.turb_pos_x, case.turb_pos_y, case.turb_pos_z))
    da = get_normalised_dims(da, transect.attrs["$D$"])
    da = get_normalised_data_deficit(da,
                                     transect.attrs["$U_\\infty$"],
                                     "$\gamma_0$")
    
    return da

case = MycekStudy()
template = Template()
runner = Runner(get_d3d_bin_path())
report = Report(79, "%d %B %Y")
validate = Validate(case)
centreline_transect = validate[0]

report_dir = Path("validation_report")
report_dir.mkdir(exist_ok=True)

with tempfile.TemporaryDirectory() as tmpdirname:

    # Create the project and then run it
    template(case, tmpdirname)
    runner(tmpdirname)

    # Pick up the results
    result = Result(tmpdirname)
    
    # Compare centreline
    centreline_sim = result.faces.extract_z(-1, **centreline_transect)
    centreline_true = centreline_transect.to_xarray()

# Add report section with plot
report.content.add_heading( f"{centreline_transect.attrs['description']}",
                           level=2)

centreline_true_gamma0 = get_gamma0(centreline_true,
                                    case,
                                    centreline_true)
centreline_sim_gamma0 = get_gamma0(centreline_sim["$u$"],
                                   case,
                                   centreline_true)

fig, ax = plt.subplots()
centreline_sim_gamma0.plot(ax=ax, x="$x^*$")
centreline_true_gamma0.plot(ax=ax, x="$x^*$")

plot_name = "centreline.png"
plot_path = report_dir / plot_name
plt.savefig(plot_path)

report.content.add_image(plot_name, "$\gamma_0$ comparison")

report.title = "Validation Example"
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
