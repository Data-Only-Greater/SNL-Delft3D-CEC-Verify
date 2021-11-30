from setuptools import setup

setup(name='SNL-Delft3D-CEC-Verify',
      version='0.1',
      description='SNL-Delft3D-CEC-Verify',
      author='Mathew Topper',
      author_email='mathew.topper@dataonlygreater.com',
      packages=['snl_d3d_cec_verify'],
      package_data={'snl_d3d_cec_verify': ['templates/fm/*.*']},
      python_requires='>=3.9',
      install_requires=['geopandas',
                        'jinja2',
                        'netCDF4',
                        'numpy',
                        'pandas',
                        'scipy',
                        'shapely',
                        'xarray'],
      zip_safe=False)
