#!/usr/bin/env python
from distutils.command.build_py import build_py
import os

from setuptools import setup, find_packages

import eulxml

class build_py_with_ply(build_py):
    '''Use ply to generate parsetab and lextab modules.'''

    def run(self, *args, **kwargs):
        # importing this forces ply to generate parsetab/lextab
        import eulxml.xpath.core
        build_py.run(self, *args, **kwargs)

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing :: Markup :: XML',
]

LONG_DESCRIPTION = None
try:
    # read the description if it's there
    with open('README.rst') as desc_f:
        LONG_DESCRIPTION = desc_f.read()
except:
    pass

setup(
    cmdclass={'build_py': build_py_with_ply},

    name='eulxml',
    version=eulxml.__version__,
    author='Emory University Libraries',
    author_email='libsysdev-l@listserv.cc.emory.edu',
    url='https://github.com/emory-libraries/eulxml',
    license='Apache License, Version 2.0',
    packages=find_packages(),

    setup_requires=[
        'ply',
    ],
    install_requires=[
        'ply',
        'lxml',
        'six<=1.10',
    ],
    extras_require={
        'django': ['Django'],
        'rdf': ['rdflib>=3.0'],
        'dev': [
            'sphinx',
            'coverage',
            'Django',
            'rdflib>=3.0',
            'mock',
            'nose',
            'unittest2',  # for python 2.6
            'tox',
        ]
        # NOTE: dev requirements should be duplicated in pip-dev-req.txt
        # for generating documentation on readthedocs.org
    },

    description='XPath-based XML data binding, with Django form support',
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
)
