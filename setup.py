#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    'six'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='layeredconfig',
    version='0.1.0',
    description='Manages configuration coming from config files, environment variables, command line arguments, code defaults or other sources',
    long_description=readme + '\n\n' + history,
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
    keywords='layeredconfig',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
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
    ],
    test_suite='tests',
    tests_require=test_requirements
)
