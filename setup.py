#!/usr/bin/env python
from setuptools import setup, find_packages

packages = find_packages(exclude=['maint'])
version_str = '4.0rc4'

setup(  name='ConceptNet',
        version=version_str,
        description='A Python API to a Semantic Network Representation of the Open Mind Common Sense Project',
        author='Catherine Havasi, Robert Speer, Jason Alonso, and Kenneth Arnold',
        author_email='conceptnet@media.mit.edu',
        url='http://conceptnet.media.mit.edu/',
        packages=packages,
        include_package_data=False,
        namespace_packages = ['csc'],
        install_requires=['csc-utils', 'django', 'south'],
        package_data={'csc.nl': ['mblem/*.pickle', 'en/*.txt', 'es/stop.txt',
                                 'hu/stop.txt', 'nl/stop.txt', 'pt/stop.txt']},

        # Metadata
        license = "GPL v3",
        )
