from setuptools import setup

setup(name='SNL-Delft3D-CEC-Verify',
      version='0.1',
      description='SNL-Delft3D-CEC-Verify',
      author='Mathew Topper',
      author_email='mathew.topper@dataonlygreater.com',
      packages=['snl_d3d_cec_verify'],
      python_requires='>=3.9',
      install_requires=[
          'jinja2',
          'netCDF4',
          'numpy',
          'shapely'
          ],
      zip_safe=False)
