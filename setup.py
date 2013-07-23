from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
import os
import re


# v = open(os.path.join(os.path.dirname(__file__), 'resourceful', '__init__.py'))
# VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(v.read()).group(1)
# v.close()
VERSION = "0.1"

readme = os.path.join(os.path.dirname(__file__), 'README.rst')

requires = [
    # "resourceful >= 0.1", commented out because 0.1 is not a valid release on pypi yet
    "pyramid >= 1.4.2"
]


setup(name='pyramid_resourceful',
      version=VERSION,
      description="Pyramid tween to integrate resourceful resource/asset management.",
      long_description=open(readme).read(),
      classifiers=[
      ],
      keywords='',
      author='Jon Rosebaugh',
      author_email='jon@inklesspen.com',
      url='',
      license='MIT',
      packages=find_packages('.', exclude=['examples*', 'test*']),
      include_package_data=True,
      tests_require = [],
      # test_suite = "nose.collector",
      zip_safe=True,
      install_requires=requires,
      entry_points = {}
)
