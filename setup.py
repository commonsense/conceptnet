#!/usr/bin/env python
from setuptools import setup, find_packages

packages = find_packages(exclude=['maint'])
version_str = '4.0.0'

setup(  name='ConceptNet',
        version=version_str,
        description='A Python API to a Semantic Network Representation of the Open Mind Common Sense Project',
        author='Catherine Havasi, Robert Speer, Jason Alonso, and Kenneth Arnold',
        author_email='conceptnet@media.mit.edu',
        url='http://conceptnet.media.mit.edu/',
        packages=packages,
        include_package_data=False,
        install_requires=['csc-utils >= 0.6', 'django', 'south', 'simplenlp'],
        # Metadata
        license = "GPL v3",
        )
