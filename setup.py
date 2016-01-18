#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

badges = open('BADGES.rst').read()
readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    'six',
    'PyYAML',
    'requests'
]

if sys.version_info < (2, 7, 0):
    requirements.append('ordereddict >= 1.1')

test_requirements = [
    # TODO: put package test requirements here
]


# we can't just "import layeredconfig" to get at
# layeredconfig.__version__ since it might have unmet dependencies at
# this point. Exctract it directly from the file (code from rdflib:s
# setup.py)
def find_version(filename):
    import re
    _version_re = re.compile(r'__version__ = "(.*)"')
    for line in open(filename):
        version_match = _version_re.match(line)
        if version_match:
            return version_match.group(1)

setup(
    name='layeredconfig',
    version=find_version('layeredconfig/__init__.py'),
    description='Manages configuration coming from config files, environment variables, command line arguments, code defaults or other sources',
    long_description=badges + "\n\n" + readme + '\n\n' + history,
    author='Staffan Malmgren',
    author_email='staffan.malmgren@gmail.com',
    url='https://github.com/staffanm/layeredconfig',
    packages=[
        'layeredconfig',
    ],
    package_dir={'layeredconfig':
                 'layeredconfig'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='configuration',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
