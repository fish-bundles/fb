#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of fish-bundles.
# https://github.com/fish-bundles/fb

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2014 Bernardo Heynemann heynemann@gmail.com


from setuptools import setup, find_packages
from fish_bundles import __version__

tests_require = [
    'mock',
    'nose',
    'coverage',
    'yanc',
    'preggy',
    'tox',
    'ipdb',
    'coveralls',
    'sphinx',
]

setup(
    name='fish-bundles',
    version=__version__,
    description='fb is the command line tool for fish-bundles',
    long_description='''
fb is the command line tool for fish-bundles.
''',
    keywords='fish fish-bundles cli shell',
    author='Bernardo Heynemann',
    author_email='heynemann@gmail.com',
    url='https://github.com/fish-bundles/fb',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Unix',
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: PyPy",
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'cliff==1.6.1',
        'blessings==1.5.1',
        'semantic_version==2.3.0',
    ],
    extras_require={
        'tests': tests_require,
    },
    entry_points={
        'console_scripts': [
            # add cli scripts here in this form:
            'fb=fish_bundles.cli:main',
        ],
        'fb': [
            'install = fish_bundles.cli.install:Install',
            'init = fish_bundles.cli.init:Init',
            'list = fish_bundles.cli.list:List',
        ],
    },
)
