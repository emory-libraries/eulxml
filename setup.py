#!/usr/bin/env python
from distutils.command.build_py import build_py
import os, glob, fnmatch
import sys
from StringIO import StringIO
from setuptools import setup, find_packages
from lxml import etree
import eulxml
import urllib


XSD_SCHEMAS = ['http://www.loc.gov/standards/mods/v3/mods-3-4.xsd', 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
               'http://www.loc.gov/standards/xlink/xlink.xsd', 'http://www.loc.gov/standards/premis/premis.xsd',
               'http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd', 'http://www.tei-c.org/release/xml/tei/custom/schema/xsd/tei_all.xsd', 'http://www.archives.ncdcr.gov/mail-account.xsd']


def grab_xsd_xml():
    types = ('*.xml', '*.xsd')
    grab_files = []
    for file in types:
        grab_files.extend(glob.glob(file))

    return grab_files

def download_schemas():
    print "Downloading schemas..."
    for schema in XSD_SCHEMAS:
        try:
            urllib.FancyURLopener().retrieve(schema, "eulxml/schema_data/" + schema.split('/')[-1])
            print "Downloaded schema: %s" % schema.split('/')[-1]
        except urllib.FancyURLopener.http_error as err:
            print "We couldn't download this schema: %s" % schema.split('/')[-1]
            print(err.code)

def generate_catalog():
    print "Generating a new catalog"

    NS_A = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
    # create XML catalog
    root = etree.parse(StringIO('''<?xml version="1.0"?><!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN" "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd"> <catalog>test</catalog>'''))

    catalog = root.Element('{%s}catalog' % (NS_A), nsmap={None: NS_A})
    
    # adding uris to catalog
    for schema in XSD_SCHEMAS:
        child = etree.Element('uri')
        catalog.append(child)
        child.attrib['name']= schema
        child.attrib['uri']= "eulxml/schema_data/" + schema.split('/')[-1]
    with open('eulxml/schema_data/catalog.xml','w') as f:
        f.write(etree.tostring(root,pretty_print=True))
    # adding comments to all schemas and generated catalog
    path = 'eulxml/schema_data'
    for filename in os.listdir(path):
        if not filename.endswith(tuple(['.xml','.xsd'])): continue
        fullname = os.path.join(path, filename)
        tree = etree.parse(fullname)
        tree.getroot().append(etree.Comment('dowloaded by eulxml on ' + time.strftime("%d/%m/%Y")))
        with open(fullname,'w') as f:
            f.write(etree.tostring(tree,pretty_print=True))


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
