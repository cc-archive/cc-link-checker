#! /usr/bin/env python3
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
  license="MIT",
  packages=['link_checker'],
  tests_require=['pytest'],
  entry_points={
    'console_scripts': ['link_checker=__main__:main']
  }
)
