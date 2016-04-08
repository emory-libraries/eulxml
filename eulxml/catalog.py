import os, glob, fnmatch
import sys
from StringIO import StringIO
from lxml import etree
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
    root = etree.parse(StringIO('''<?xml version="1.0"?><!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN" "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd"> <catalog></catalog>'''))

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

