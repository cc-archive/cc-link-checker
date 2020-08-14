#!/usr/bin/env python3
from setuptools import setup

setup(
    name="link_checker",
    version="0.1.0",
    author="Creative Commons",
    description=(
        "Checks links across creativecommons.org for "
        "license legalcode, deeds, and rdf files"
    ),
    url="https://github.com/creativecommons/cc-link-checker",
    install_requires=[
        "beautifulsoup4",
        "grequests",
        "importlib-metadata",
        "junit-xml",
        "lxml",
        "requests",
    ],
    license="MIT",
    tests_require=["pytest"],
    packages=["link_checker"],
    entry_points={
        "console_scripts": ["link_checker=link_checker.__main__:main"]
    },
    include_package_data=True,
)
