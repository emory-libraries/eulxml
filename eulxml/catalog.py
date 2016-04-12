"""Catalog.py is run upon the the build of eulxml to generate catalog.xml and schemas"""
# file eulxml/catalog.py
#
#   Copyright 2010,2011 Emory University Libraries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import os
import glob
import urllib
import time
from lxml import etree
from eulxml import xmlmap


XSD_SCHEMAS = ['http://www.loc.gov/standards/mods/v3/mods-3-4.xsd',
               'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
               'http://www.loc.gov/standards/xlink/xlink.xsd',
               'http://www.loc.gov/standards/premis/premis.xsd',
               'http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd',
               'http://www.tei-c.org/release/xml/tei/custom/schema/xsd/tei_all.xsd']
# , 'http://www.archives.ncdcr.gov/mail-account.xsd'

class Uri(xmlmap.XmlObject):
    """This class is to generate Uris for the catalog"""
    ROOT_NAME = 'uri'
    ROOT_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
    name = xmlmap.StringField('@name')
    uri = xmlmap.StringField('@uri')

class Catalog(xmlmap.XmlObject):
    """Catalog is xmlobject to create a catalog for all xml schemas"""
    ROOT_NAME = 'catalog'
    ROOT_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
    ROOT_NAMESPACES = {'c' : ROOT_NS}
    uri_list = xmlmap.NodeListField('c:uri', Uri)

def download_schemas():
    """Downloading schemas from corresponding urls."""
    print "Downloading schemas..."
    for schema in XSD_SCHEMAS:
        try:
            urllib.FancyURLopener().retrieve(schema, "eulxml/schema_data/" + schema.split('/')[-1])
            print "Downloaded schema: %s" % schema.split('/')[-1]
        except urllib.FancyURLopener.http_error as err:
            print "We couldn't download this schema: %s" % schema.split('/')[-1]
            print(err.code)

def generate_catalog():
    """Generating catalog from dowloaded schemas"""
    print "Generating a new catalog"
    catalog = Catalog()
    # adding uris to catalog
    for schema in XSD_SCHEMAS:
        catalog.uri_list.append(Uri(name=schema, uri="eulxml/schema_data/" + schema.split('/')[-1]))

    root = etree.fromstring(catalog.serialize())
    with open('eulxml/schema_data/catalog.xml', 'w') as xml_catalog:
        xml_catalog.write(etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8", doctype="<!DOCTYPE TEST_FILE>"))
        xml_catalog.close()

    # adding comments to all schemas and generated catalog
    path = 'eulxml/schema_data'
    for filename in os.listdir(path):
        if not filename.endswith(tuple(['.xml', '.xsd'])):
            continue
        fullname = os.path.join(path, filename)
        print fullname
        tree = etree.parse(fullname)
        tree.getroot().append(etree.Comment('dowloaded by eulxml on ' + time.strftime("%d/%m/%Y")))
        with open(fullname, 'w') as xml_catalog:
            xml_catalog.write(etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="UTF-8", doctype="<!DOCTYPE TEST_FILE>"))

