#!/usr/bin/env python
from distutils.command.build_py import build_py
import os, glob, fnmatch
import sys
from StringIO import StringIO
from setuptools import setup, find_packages
from lxml import etree
import eulxml
from eulxml.catalog import download_schemas, generate_catalog
import urllib

XSD_SCHEMAS = ['http://www.loc.gov/standards/mods/v3/mods-3-4.xsd', 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
               'http://www.loc.gov/standards/xlink/xlink.xsd', 'http://www.loc.gov/standards/premis/premis.xsd',
               'http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd', 'http://www.tei-c.org/release/xml/tei/custom/schema/xsd/tei_all.xsd', 'http://www.archives.ncdcr.gov/mail-account.xsd']

# getting catalog files 
def get_catalog_files():

    if not os.path.exists('eulxml/schema_data/catalog.xml'):
        print "There is no catalog. :("
        counter = 0 
        for fname in XSD_SCHEMAS:
            if os.path.isfile("eulxml/schema_data/" + fname.split('/')[-1]):
                counter += 1

        print "Do we need to download schemas?"
        if counter != len(XSD_SCHEMAS):
            print "yes, we do. Downloading..."
            download_schemas()

        print "Generating catalog..."
        generate_catalog()
        
    else:
        print "Found one!"
    
    #grab 
    return grab_xsd_xml()

files = get_catalog_files()

class build_py_with_ply(build_py):
    '''Use ply to generate parsetab and lextab modules.'''

    def run(self, *args, **kwargs):
        # importing this forces ply to generate parsetab/lextab
        import eulxml.xpath.core
        build_py.run(self, *args, **kwargs)

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
]
# NOTE: dev requirements should be duplicated in pip-dev-req.txt
# for generating documentation on readthedocs.org

# unittest2 should only be included for py2.6
if sys.version_info < (2, 7):
    dev_requirements.append('unittest2')


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
        'ply>=3.8',
    ],
    install_requires=[
        'ply',
        'lxml',
        'six>=1.10',
    ],
    extras_require={
        'django': ['Django<1.9'],
        'rdf': ['rdflib>=3.0'],
        'dev': dev_requirements
    },
    data_files = files,
    description='XPath-based XML data binding, with Django form support',
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
)
