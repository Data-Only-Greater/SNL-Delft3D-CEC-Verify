# Documentation Build Instructions

HTML documentation is built using the [Sphinx][1] documentation system, with the 
[sphinx-autodoc-typehints][2] plugin and the [insipid][3] theme.

## Dependency Installation

```
(base) > conda activate _snld3d
(_snld3d) > conda install sphinx sphinx-autodoc-typehints
(_snld3d) > pip install insipid-sphinx-theme
```

## Local Build

Activate the conda environment and move to the `docs` directory

```
(base) > conda activate _snld3d
(_snld3d) > cd docs
```

Then for Windows,

```
(_snld3d) > .\make.bat HTML
```

Alternatively for Linux

```
(_snld3d) > make HTML
```

The documentation can then be opened at the path `docs/_build/html/index.html`.

[1]: https://www.sphinx-doc.org/en/master/
[2]: https://github.com/tox-dev/sphinx-autodoc-typehints
[3]: https://insipid-sphinx-theme.readthedocs.io/
