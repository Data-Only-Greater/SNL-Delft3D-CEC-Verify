[![python](https://img.shields.io/badge/dynamic/yaml?label=python&query=%24.jobs.pytest.strategy.matrix[%27python-version%27][:]&url=https%3A%2F%2Fraw.githubusercontent.com%2FData-Only-Greater%2FSNL-Delft3D-CEC-Verify%2Fmain%2F.github%2Fworkflows%2Funit_tests.yml)](https://www.python.org/)
[![platform](https://img.shields.io/badge/dynamic/yaml?label=os&query=%24.jobs.pytest.strategy.matrix.os[:]&url=https%3A%2F%2Fraw.githubusercontent.com%2FData-Only-Greater%2FSNL-Delft3D-CEC-Verify%2Fmain%2F.github%2Fworkflows%2Funit_tests.yml)](https://en.wikipedia.org/wiki/Usage_share_of_operating_systems#Desktop_and_laptop_computers)

[![unit tests](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/unit_tests.yml)
[![static type checks](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/static_type_checks.yml/badge.svg)](https://github.com/Data-Only-Greater/SNL-Delft3D-CEC-Verify/actions/workflows/static_type_checks.yml)

[![codecov](https://codecov.io/gh/Data-Only-Greater/SNL-Delft3D-CEC-Verify/branch/main/graph/badge.svg?token=JJCDDVNPS6)](https://codecov.io/gh/Data-Only-Greater/SNL-Delft3D-CEC-Verify)

# SNL-Delft3D-CEC-Verify

SNL-Delft3D-CEC-Verify is a python package for automated testing of 
[SNL-Delft3D-FM-CEC][2] which adds current energy converter (CEC) support to 
the [Delft3D Flexible Mesh Suite][3]. This package is used to verify the 
performance of SNL-Delft3D-FM-CEC by comparing against the 2014 flume 
experiment conducted by Mycek et al.[[1]](#1).

## Installation

:warning: This repository uses [Git LFS][8] to store large files, so if you
want to clone the repository, make sure to use `git lfs clone` to download all
of the files and set up LFS.

The preferred method of installation is to use [Anaconda Python][4]. Download
this package, open an Anaconda prompt and then change directory into the
package root. Now create a conda environment using the following command:

```
(base) > conda env create --file environment.yml
```

Activate the `_snld3d` environment and then install the package:

```
(base) > conda activate _snld3d
(_snld3d) > pip install --no-deps -e .
```

## Example

A short example is provided in the `examples` folder, named `basic.py`. Some
plots are generated which requires the `matplotlib` library. To install it,
type:

```
(_snld3d) > conda install -y matplotlib
```

The example generates a report in [Pandoc][5] markdown format. This report
can be optionally converted to Word format if the `pypandoc` package is 
installed. To install it, type:

```
(_snld3d) > conda install -y pypandoc
```

Currently, a compiled copy of SNL-Delft3D-FM-CEC must be available for the 
examples to run. If the binaries are installed in the standard location in the 
Delft3D source code (i.e. in the `src/bin` folder), simply copy the `basic.py` 
file (and `reference.docx` file if converting to Word) to the source code's 
`examples` directory. Alternatively, the location of SNL-Delft3D-FM-CEC 
binaries can specified by setting the `D3D_BIN` environment variable, instead 
of copying the example files. To set `D3D_BIN`, for example, using PowerShell:

```
(_snld3d) > $env:D3D_BIN = "\path\to\SNL-Delft3D-FM-CEC\src\bin"
```

To run the example, move to the directory containing `basic.py` and then 
call Python:

```
(_snld3d) > python basic.py
```

If successful, the report files (and images) will be placed in a sub-directory
called `basic_report`.

Currently, the `basic.py` file is the only indicative documentation of how
`SNL-Delft3D-CEC-Verify` is used. Improved documentation of the available 
features will be forthcoming in the near future.

## Testing

To run unit and type testing on the package, first install the required
dependencies:

```
(_snld3d) > conda install -y mypy pytest pytest-mock
```

To run the unit tests, type the following from the root directory:

```
(_snld3d) > pytest
```

To run the type tests, type the following from the root directory:

```
(_snld3d) > mypy src
```

## Uninstall

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

Some of the code in this package is derived from the [delft3dfmpy][6] and
[django][7] projects.

## References

<a id="1">[1]</a> 
Mycek, P., Gaurier, B., Germain, G., Pinon, G., & Rivoalen, E. (2014).
Experimental study of the turbulence intensity effects on marine current turbines behaviour. Part I: One single turbine.
Renewable Energy, 66, 729–746.

[2]: https://github.com/SNL-WaterPower/SNL-Delft3D-FM-CEC
[3]: https://www.deltares.nl/en/software/delft3d-flexible-mesh-suite/
[4]: https://www.anaconda.com/products/individual
[5]: https://pandoc.org/
[6]: https://github.com/openearth/delft3dfmpy
[7]: https://github.com/django/django
[8]: https://git-lfs.github.com/
