#!/usr/bin/env python
"""Setup.py for eulxml package"""
from distutils.command.build_py import build_py
from distutils.command.clean import clean
from distutils.command.sdist import sdist
from distutils.core import Command
import os
import sys
import shutil
from setuptools import setup, find_packages
import eulxml


class GenerateXmlCatalog(Command):
    '''Custom setup command to generate fresh catalog and schemas'''
    user_options = []

    def initialize_options(self):
        """init options"""
        pass

    def finalize_options(self):
        """finalize options"""
        pass

    def run(self):
        from eulxml.catalog import generate_catalog
        generate_catalog()


def generate_catalog_if_needed():
    # helper method to check if catalog is present, and generate if not
    if not os.path.exists(eulxml.XMLCATALOG_FILE):
        from eulxml.catalog import generate_catalog
        print("Cenerating XML catalog...")
        generate_catalog()



class CleanSchemaData(clean):
    """Custom cleanup command to delete build and schema files"""
    description = "Custom clean command; remove schema files and XML catalog"

    def run(self):
        # remove schema data and then do any other normal cleaning
        try:
            shutil.rmtree(eulxml.XMLCATALOG_DIR)
        except OSError:
            pass
        clean.run(self)


class BuildPyWithPly(build_py):
    """Use ply to generate parsetab and lextab modules."""

    def run(self):
        # importing this forces ply to generate parsetab/lextab
        import eulxml.xpath.core

        generate_catalog_if_needed()

        build_py.run(self)


class SdistWithCatalog(sdist):
    """Extend sdist command to ensure schema catalog is included."""

    def run(self):
        generate_catalog_if_needed()
        sdist.run(self)


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
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

dev_requirements = [
    'sphinx>=1.3.5',
    'coverage',
    'Django<1.9',
    'rdflib>=3.0',
    'mock',
    'nose',
    'tox',
    'requests',
]
# NOTE: dev requirements should be duplicated in pip-dev-req.txt
# for generating documentation on readthedocs.org

# unittest2 should only be included for py2.6
if sys.version_info < (2, 7):
    dev_requirements.append('unittest2')


setup(
    cmdclass={
        'build_py': BuildPyWithPly,
        'clean': CleanSchemaData,
        'sdist': SdistWithCatalog,
        'xmlcatalog': GenerateXmlCatalog
    },

    name='eulxml',
    version=eulxml.__version__,
    author='Emory University Libraries',
    author_email='libsysdev-l@listserv.cc.emory.edu',
    url='https://github.com/emory-libraries/eulxml',
    license='Apache License, Version 2.0',
    packages=find_packages(),

    setup_requires=[
        'ply>=3.8',
    ],
    install_requires=[
        'ply>=3.8',
        'lxml>=3.4',
        'six>=1.10',
    ],
    extras_require={
        'django': ['Django<1.9'],
        'rdf': ['rdflib>=3.0'],
        'dev': dev_requirements
    },
    package_data={'eulxml': [
        # include schema catalog and all downloaded schemas in the package
        '%s/*' % eulxml.SCHEMA_DATA_DIR
    ]},
    description='XPath-based XML data binding, with Django form support',
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
)
