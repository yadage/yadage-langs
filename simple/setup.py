import os
from setuptools import setup, find_packages

setup(
  name = 'yadage-haiku',
  version = '0.15.1',
  description = 'yadage-haiku - a very concise dialect of yadage.',
  url = '',
  author = 'Lukas Heinrich',
  author_email = 'lukas.heinrich@cern.ch',
  packages = find_packages(),
  include_package_data = True,
  install_requires = [
    'yadage-schemas',
    'pyyaml'
  ],
  entry_points = {
      'console_scripts': [
      ],
  },
  dependency_links = [
  ]
)
