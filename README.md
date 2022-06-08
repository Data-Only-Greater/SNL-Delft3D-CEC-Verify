[![python](https://img.shields.io/badge/dynamic/yaml?label=python&query=%24.jobs.pytest.strategy.matrix[%27python-version%27][:]&url=https%3A%2F%2Fraw.githubusercontent.com%2FData-Only-Greater%2FSNL-Delft3D-CEC-Verify%2Fmain%2F.github%2Fworkflows%2Funit_tests.yml)](https://www.python.org/)
[![platform](https://img.shields.io/badge/dynamic/yaml?label=os&query=%24.jobs.pytest.strategy.matrix.os[:]&url=https%3A%2F%2Fraw.githubusercontent.com%2FData-Only-Greater%2FSNL-Delft3D-CEC-Verify%2Fmain%2F.github%2Fworkflows%2Funit_tests.yml)](https://en.wikipedia.org/wiki/Usage_share_of_operating_systems#Desktop_and_laptop_computers)

[![unit tests](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/unit_tests.yml)
[![static type checks](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/static_type_checks.yml/badge.svg)](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/static_type_checks.yml)
[![documentation](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/docs.yml/badge.svg)](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/docs.yml)
[![packaging](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/package.yml/badge.svg)](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/package.yml)

[![codecov](https://codecov.io/gh/Data-Only-Greater/SNL-Delft3D-CEC-Verify/branch/main/graph/badge.svg?token=JJCDDVNPS6)](https://codecov.io/gh/Data-Only-Greater/SNL-Delft3D-CEC-Verify)
[![Conda](https://img.shields.io/conda/v/dataonlygreater/snl-delft3d-cec-verify?label=conda)](https://anaconda.org/dataonlygreater/snl-delft3d-cec-verify)

# SNL-Delft3D-CEC-Verify

SNL-Delft3D-CEC-Verify is a python package for automated testing of 
[SNL-Delft3D-CEC][116] and [SNL-Delft3D-FM-CEC][101] which adds current energy 
converter (CEC) support to the [Delft3D 4 (structured)][117] and [Delft3D 
Flexible Mesh][102] suites, respectively. This package  is used to verify the 
performance of SNL-Delft3D-CEC and SNL-Delft3D-FM-CEC by comparing against the 
2014 flume experiment conducted by Mycek et al.[[1]](#1).

## Quick Start

### Python Distribution

Due to the many non-Python binary requirements of the package dependencies, 
installation requires the use of [Anaconda Python][103] or a fully free-to-use 
equivalent, such as [Miniforge][114].

### Install

From a conda prompt create a named environment in which to install the 
`snl-delft3d-cec-verify` conda package and then set up the channels required 
for future updates:

```
(base) > conda create -y -n snld3d --override-channels -c conda-forge -c dataonlygreater snl-delft3d-cec-verify=0.7.0
(base) > conda activate snld3d
(snld3d) > conda config --env --add channels conda-forge --add channels dataonlygreater
(snld3d) > conda config --env --set channel_priority strict
```

After this, working with SNL-Delft3D-CEC-Verify requires that the `snld3d`
environment be activated:

```
(base) > conda activate snld3d
(snld3d) >
```

### Update

To update to the latest version of the conda package, using the `snld3d` 
environment, type:

```
(snld3d) > conda update -y snl-delft3d-cec-verify
```

### Minimal Working Example

The following presents an example of running a case study using a flexible mesh
 (`"fm"`) model, based on the Mycek experiment, and collecting results at the 
turbine centre. Note that the token `<D3D_BIN>`, should be replaced with the 
path to the `bin` directory of the compiled Delft3D source code.

```pycon
>>> import tempfile
>>> from snl_d3d_cec_verify import MycekStudy, Result, Runner, Template
>>> template = Template()
>>> runner = Runner(<D3D_BIN>)
>>> case = MycekStudy()
>>> with tempfile.TemporaryDirectory() as tmpdirname:
...     template(case, tmpdirname)
...     runner(tmpdirname)
...     result = Result(tmpdirname)
...     print(result.faces.extract_turbine_centre(-1, case))
Dimensions:  (dim_0: 1)
Coordinates:
    $z$      int32 -1
    time     datetime64[ns] 2001-01-01T01:00:00
    $x$      (dim_0) int32 6
    $y$      (dim_0) int32 3
Dimensions without coordinates: dim_0
Data variables:
    k        (dim_0) float64 0.9993
    $u$      (dim_0) float64 0.7147
    $v$      (dim_0) float64 4.467e-17
    $w$      (dim_0) float64 -0.002604

```

To use a structured model in the above example, change line 3 to:

```
>>> template = Template("structured")
```

More detailed examples are provided in the section below.

## Examples

### Prerequisites

Examples are provided in the `examples.zip` asset of the [latest 
release][118]. Alternatively, they can be found in the `examples` folder of 
the source code. Each example can be run using either the flexible mesh or 
structured grid models.

As plots are generated in the examples, the `matplotlib` library is also 
required. To install it, type:

```
(snld3d) > conda install -y matplotlib
```


The examples generate reports in [Pandoc][104] markdown format. These reports 
can be optionally converted to Word format if the `pypandoc` package is 
installed. To install it, type:

```
(snld3d) > conda install -y pypandoc pandoc
```

Currently, a compiled copy of SNL-Delft3D-CEC or SNL-Delft3D-FM-CEC must be 
available for the examples to run. If the binaries are installed in the 
standard location in the Delft3D source code (i.e. in the `src/bin` folder), 
simply copy the required files for each example to the source code's 
`examples` directory. A list of files required to run each example is provided 
at the top of the subsections below.

Alternatively, the location of Delft3D binaries can specified by setting the 
`D3D_BIN` environment variable, instead of copying the example files. To set 
`D3D_BIN`, for example, using PowerShell:

```
(snld3d) > $env:D3D_BIN = "\path\to\SNL-Delft3D-FM-CEC\src\bin"
```

### Basic Example

Required files:
+   `basic.py`
+   `reference.docx` (for conversion to Word format)

The basic example shows how to define a flexible mesh or structured model with 
varying parameters, run the model and then analyse the results.

To run the example, move to the directory containing `basic.py` and then call 
the script using Python with the model type (either `fm` or `structured`) as 
the second argument. For instance, for the flexible mesh model call:

```
(snld3d) > python basic.py fm
```

If successful, the report files (and images) will be placed into a 
sub-directory based on the model type. For the flexible mesh model, this is 
`fm/basic_report`.

### Validation Example

Required files:
+   `validation.py`
+   `examples.bib` (for conversion to Word format)
+   `reference.docx` (for conversion to Word format)

The validation example demonstrates comparison of a flexible mesh or 
structured model with the experimental results of Mycek et al.[[1]](#1)

To run the example, move to the directory containing `validation.py` and then 
call the script using Python with the model type (either `fm` or `structured`) 
as the second argument. For instance, for the structured grid model call:

```
(snld3d) > python validation.py structured
```

If successful, the report files (and images) will be placed into a 
sub-directory based on the model type. For the structured grid model, this is 
`structured/validation_report`.

### Grid Convergence Study

Required files:
+   `grid_convergence.py`
+   `examples.bib` (for conversion to Word format)
+   `reference.docx` (for conversion to Word format)

This is the first "production" example, designed to generate meaningful 
results. A grid convergence study (see e.g. [[2]](#2)) is conducted to 
determine the free stream and turbine wake velocities at infinite grid 
resolution. The results are then compared to the results of Mycek et 
al.[[1]](#1).

This example requires the [convergence][109] package to be installed. Issue 
the following command in the conda environment:

```
(snld3d) > pip install convergence
```

To run the example, move to the directory containing `grid_convergence.py` and 
then call the script using Python with the model type (either `fm` or 
`structured`) as the second argument. For instance, for the flexible mesh 
model call:

```
(snld3d) > python grid_convergence.py fm
```

If successful, the report files (and images) will be placed into a 
sub-directory based on the model type. For the flexible mesh model, this is 
`structured/grid_convergence_report`. To avoid repeating simulations in the 
event of an unexpected failure or change to the `grid_convergence.py` file, 
the Delft3D simulations, and a copy of their case study parameters, are stored 
in a sub-directory based on the model type. For the structured grid model, for 
example, this is `structured/runs`. If the Delft3D solver is updated, ensure to 
delete or move this folder, so that new simulations are conducted.

By default, the study is conducted using just one CPU thread. To reduce 
simulation time of the `fm` model, assuming additional capacity is available, 
increase the number of utilised threads using the `--threads` optional argument:

```
(snld3d) > python grid_convergence.py fm --threads 8
```

Note that this study takes a considerable amount of wall-clock time to 
complete. On an [Intel i7-4790][108], the full study required 78 hours. To run 
an incomplete study, with a more tractable time scale, use the `--experiments` 
optional argument to reduce the number of experiments. For example:

```
(snld3d) > python grid_convergence.py fm --threads 8 --experiments 3
```

Pre-calculated results of the full study are available in the [online 
documentation][110].

### Model Comparison Study

Required files:
+   `comparison.py`
+   `examples.bib` (for conversion to Word format)
+   `reference.docx` (for conversion to Word format)

The second production example is a comparison of the flexible mesh and 
structured grid solvers for a turbine simulation using identical settings.

This example uses the [pandoc-crossref][119] package to reference sections
and figures within the generated report. To install the package (for converting
to Word format with pypandoc) issue the following command:

```
(snld3d) > conda install pandoc-crossref=0.3.10.0
```

For the example to run, two environment variable **must be set**. For path to 
the flexible mesh solver, set the `D3D_FM_BIN` variable. In PowerShell, for 
example:

```
(snld3d) > $env:D3D_FM_BIN = "\path\to\SNL-Delft3D-FM-CEC\src\bin"
```

For the path to the structured grid solver, set the `D3D_4_BIN` environment
variable. In PowerShell again:

```
(snld3d) > $env:D3D_4_BIN = "\path\to\SNL-Delft3D-CEC\src\bin"
```

Then move to the directory containing `comparison.py` and call the script using 
Python:

```
(snld3d) > python comparison.py
```

If successful, the report files (and images) will be placed into a 
sub-directory called `comparison_report`. To avoid repeating simulations, the 
Delft3D simulations, and a copy of their case study parameters, are stored in 
a sub-directory based on the model type. For the flexible mesh model this is 
`fm/runs` and for the structured grid model it's `structured/runs`. If 
either Delft3D solver is updated, ensure to delete or move these folders, so 
that new simulations are conducted.

By default, the study is conducted using just one CPU thread. To reduce 
simulation time of the `fm` model, assuming additional capacity is available, 
increase the number of utilised threads using the `--threads` optional argument:

```
(snld3d) > python comparison.py --threads 8
```

Note that this study takes a considerable amount of wall-clock time to 
complete. To run the simulations at lower resolution (and, therefore, more 
rapidly), use the `--grid-resolution` optional argument. For example:

```
(snld3d) > python comparison.py --threads 8 --grid-resolution 0.25
```

Pre-calculated results of the study at the default resolution of 0.0625m is 
available in the [online documentation][110].

## Documentation

API documentation, which describes the classes and functions used in the 
examples, can be found [here][107]. Documentation updates are ongoing. 

## Development

### Installation

:warning: This repository uses [Git LFS][106] to store large files, so make 
sure to use `git lfs clone` when cloning the repository to download all of the 
files and set up LFS. For example:

```
> git lfs clone https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify.git
```

Due to the many non-Python binary requirements of the package dependencies, 
installation requires the use of [Anaconda Python][103] or a fully free-to-use 
equivalent, such as [Miniforge][114]. Open a conda prompt and then change 
directory into the package root. Use the following commands to install the 
package, testing and documentation dependencies into the `_snld3d` environment.

```
(base) > conda env create --file .conda/environment.yml
```

Activate the `_snld3d` environment, setup the channels, and then install the 
SNL-Delft3D-CEC-Verify package in development mode:

```
(base) > conda activate _snld3d
(_snld3d) > conda config --env --add channels conda-forge
(_snld3d) > conda config --env --set channel_priority strict
(_snld3d) > pip install --no-deps -e .
```

### Testing

To run the unit tests and get a coverage report, type the following from the 
root directory:

```
(_snld3d) > pytest --cov-report term-missing --cov="./src/snl_d3d_cec_verify/"
```

To run the type tests, type the following from the root directory:

```
(_snld3d) > mypy --install-types --non-interactive src
```

To run doctests, type the following from the root directory:

```
(_snld3d) > pytest --doctest-modules src
```

To run all three test suites simultaneously, invoke tox from the root directory:

```
(_snld3d) > tox
```

Note that tox creates a dedicated environment for the tests, which can be time 
consuming on first run (or if there are any dependency changes).

### Documentation

HTML documentation is built using the [Sphinx][111] documentation system, with 
the [sphinx-autodoc-typehints][112] plugin and the [insipid][113] theme.

To build the documentation locally, activate the conda environment and move to
the `docs` directory:

```
(base) > conda activate _snld3d
(_snld3d) > cd docs
```

Then to build, for Windows:

```
(_snld3d) > .\make.bat html
```

Alternatively for Linux

```
(_snld3d) > make html
```

The documentation can then be opened at the path `docs/_build/html/index.html`.

### Versioning

Use [python-semantic-release][115] to update version numbers in the package.
For instance, to add a commit that bumps the patch version, call:

```
(_snld3d) > semantic-release version --patch
```

### Uninstall

To remove the conda environment containing SNL-Delft3D-CEC-Verify, open an
Ananconda prompt and type:

```
(base) > conda remove --name _snld3d --all
```

You may need to deactivate the `_snld3d` environment first, if it is still
open, by typing:

```
(_snld3d) > conda deactivate
(base) > conda remove --name _snld3d --all
```

## Acknowledgements

:warning: Data reversed engineered from Mycek et al.[[1]](#1) is stored within 
this package. If you intend to publish results using this data, make sure to 
acknowledge its source at the point of use, e.g. _"Experimental data reverse 
engineered from Mycek et al.[[1]](#1), fig. 11a."_.

Some of the code in this package is derived from the [delft3dfmpy][105] project.

## References

<a id="1">[1]</a> 
Mycek, P., Gaurier, B., Germain, G., Pinon, G., & Rivoalen, E. (2014).
Experimental study of the turbulence intensity effects on marine current turbines behaviour. Part I: One single turbine.
Renewable Energy, 66, 729–746.

<a id="2">[2]</a> 
Examining Spatial (Grid) Convergence. (2002).
Retrieved 24 January 2022, from https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html

[101]: https://github.com/SNL-WaterPower/SNL-Delft3D-FM-CEC
[102]: https://www.deltares.nl/en/software/delft3d-flexible-mesh-suite/
[103]: https://www.anaconda.com/products/individual
[104]: https://pandoc.org/
[105]: https://github.com/openearth/delft3dfmpy
[106]: https://git-lfs.github.com/
[107]: https://data-only-greater.github.io/SNL-Delft3D-CEC-Verify/main/api/snl_d3d_cec_verify.html
[108]: https://www.intel.com/content/www/us/en/products/sku/80806/intel-core-i74790-processor-8m-cache-up-to-4-00-ghz/specifications.html
[109]: https://github.com/Data-Only-Greater/convergence
[110]: https://data-only-greater.github.io/SNL-Delft3D-CEC-Verify/main/validation/index.html
[111]: https://www.sphinx-doc.org/en/master/
[112]: https://github.com/tox-dev/sphinx-autodoc-typehints
[113]: https://insipid-sphinx-theme.readthedocs.io/
[114]: https://github.com/conda-forge/miniforge
[115]: https://python-semantic-release.readthedocs.io/en/latest/
[116]: https://github.com/SNL-WaterPower/SNL-Delft3D-CEC
[117]: https://www.deltares.nl/en/software/delft3d-4-suite/
[118]: https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/releases/latest
[119]: https://github.com/lierdakil/pandoc-crossref
