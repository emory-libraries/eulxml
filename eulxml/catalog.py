import os, glob, fnmatch
import sys
from StringIO import StringIO
from lxml import etree
import urllib
from eulxml import xmlmap
import time

XSD_SCHEMAS = ['http://www.loc.gov/standards/mods/v3/mods-3-4.xsd', 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
               'http://www.loc.gov/standards/xlink/xlink.xsd', 'http://www.loc.gov/standards/premis/premis.xsd',
               'http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd', 'http://www.tei-c.org/release/xml/tei/custom/schema/xsd/tei_all.xsd']
# , 'http://www.archives.ncdcr.gov/mail-account.xsd'

class Uri(xmlmap.XmlObject):
    ROOT_NAME = 'uri'
    ROOT_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
    name = xmlmap.StringField('@name')
    uri = xmlmap.StringField('@uri')

class Catalog(xmlmap.XmlObject):
    ROOT_NAME = 'catalog'
    ROOT_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
    ROOT_NAMESPACES = {'c' : ROOT_NS}
    uri_list = xmlmap.NodeListField('c:uri', Uri)



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
    catalog = Catalog()
    # adding uris to catalog
    for schema in XSD_SCHEMAS:
        catalog.uri_list.append(Uri(name=schema,uri="eulxml/schema_data/" + schema.split('/')[-1]))

    root = etree.fromstring(catalog.serialize())
    with open('eulxml/schema_data/catalog.xml','w') as f:
        f.write(etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8",doctype="<!DOCTYPE TEST_FILE>"))
        f.close()

    # adding comments to all schemas and generated catalog
    path = 'eulxml/schema_data'
    for filename in os.listdir(path):
        if not filename.endswith(tuple(['.xml','.xsd'])): continue
        fullname = os.path.join(path, filename)
        print fullname
        tree = etree.parse(fullname)
        tree.getroot().append(etree.Comment('dowloaded by eulxml on ' + time.strftime("%d/%m/%Y")))
        with open(fullname,'w') as f:
            f.write(etree.tostring(tree,pretty_print=True,xml_declaration=True, encoding="UTF-8",doctype="<!DOCTYPE TEST_FILE>"))

