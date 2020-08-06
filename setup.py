#! /usr/bin/env python
from setuptools import setup

setup(
  name="link_checker",
  version="0.0.1",
  author="Creative Commons",
  description=(
    "Checks links across creativecommons.org for "
    "license legalcode, deeds, and rdf files"
  ),
  url="https://github.com/creativecommons/cc-link-checker",
  install_requires=[
    'beautifulsoup4',
    'grequests',
    'importlib-metadata',
    'junit-xml',
    'lxml',
    'requests'
  ],
  packages=['link_checker'],
  tests_require=['pytest'],
  entry_points={
    'console_scripts': ['link_checker=link_checker.link-checker:main']
  },
  include_package_data=True,
)
