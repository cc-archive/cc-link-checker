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
  dependency_links=[
    'https://github.com/creativecommons/cc-link-checker/tarball/master/'
  ],
  install_requires=[
    'beautifulsoup4',
    'grequests',
    'importlib-metadata',
    'junit-xml',
    'lxml',
    'requests'
  ],
  tests_require=['pytest'],
  entry_points={'console_scripts': 'link_checker=link_checker:main'}
)
