# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
from pathlib import Path

docs_source_dir = Path(os.getenv("SPHINX_MULTIVERSION_SOURCEDIR", default="."))
package_dir = docs_source_dir / ".." / "src"
print(package_dir.resolve())
sys.path.append(str(package_dir.resolve()))

# -- Project information -----------------------------------------------------

project = 'SNL-Delft3D-CEC-Verify'
copyright = '2022, Mathew Topper'
author = 'Mathew Topper'

# The full version, including alpha/beta/rc tags
release = '0.4.3'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_autodoc_typehints',
    'sphinx.ext.intersphinx',
    'sphinx_multiversion'
]

# Autodoc configuration
autodoc_member_order = 'bysource'

# Intersphinx configuration
intersphinx_mapping = {'python': ('https://docs.python.org/3', None),
                       'geopandas': ('https://geopandas.org/en/v0.10.2/', None),
                       'jinja': ('https://jinja.palletsprojects.com/en/3.0.x/', None),
                       'numpy': ('https://numpy.org/doc/1.22/', None),
                       'pandas': ('https://pandas.pydata.org/pandas-docs/version/1.3', None),
                       'shapely': ('https://shapely.readthedocs.io/en/stable', None),
                       'xarray': ('https://xarray.pydata.org/en/v0.20.1/', None)}

# sphinx_multiversion configuration
smv_branch_whitelist = r'(main)$'
smv_remote_whitelist = r'^(origin)$'
smv_tag_whitelist = r'^v(\d+\.\d+\.\d+)$' # r'^v(?!0.4.0|0.4.1|0.4.2)\d+\.\d+\.\d+$'
smv_released_pattern = r'^refs/tags/.*$'
smv_latest_version = 'v0.4.3'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    '_assets',
    '_build',
    'Thumbs.db',
    '.DS_Store']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'insipid'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# A list of paths that contain extra files not directly related to the 
# documentation, such as robots.txt or .htaccess. Relative paths are taken as 
# relative to the configuration directory. They are copied to the output 
# directory. They will overwrite any existing file of the same name.
#html_extra_path =

# Custom sidebar templates, must be a dictionary that maps document names to
# template names.
html_sidebars = {
    '**': [
        'globaltoc.html',
        'separator.html',
        'indices.html',
        'separator.html',
        'versioning.html'
    ],
}

html_css_files = [
    'custom.css',
]
