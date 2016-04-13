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
from datetime import date
from lxml import etree
from eulxml import xmlmap, __version__, XMLCATALOG_DIR, XMLCATALOG_FILE
import logging


logger = logging.getLogger(__name__)


XSD_SCHEMAS = ['http://www.loc.gov/standards/mods/v3/mods-3-4.xsd',
               'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
               'http://www.loc.gov/standards/xlink/xlink.xsd',
               'http://www.loc.gov/standards/premis/premis.xsd',
               'http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd',
               'http://www.tei-c.org/release/xml/tei/custom/schema/xsd/tei_all.xsd']
# , 'http://www.archives.ncdcr.gov/mail-account.xsd'


class Uri(xmlmap.XmlObject):
    """:class:`xmlmap.XmlObject` class for Catalog uris"""
    ROOT_NAME = 'uri'
    ROOT_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
    #: name attribute
    name = xmlmap.StringField('@name')
    #: uri attribute
    uri = xmlmap.StringField('@uri')


class Catalog(xmlmap.XmlObject):
    """:class:`xmlmap.XmlObject` class to for generating XML Catalogs"""
    ROOT_NAME = 'catalog'
    ROOT_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
    ROOT_NAMESPACES = {'c': ROOT_NS}
    #: list of uris, as instance of :class:`Uri`
    uri_list = xmlmap.NodeListField('c:uri', Uri)



def download_schema(uri, path, comment=None):
    """Download a schema from a specified URI and save it locally."""
    # short-hand name of the schema, based on uri
    schema = os.path.basename(uri)
    try:
        urllib.FancyURLopener().retrieve(uri, path)

        # if a comment is specified, add it to the locally saved schema
        if comment is not None:
            tree = etree.parse(path)
            tree.getroot().append(etree.Comment(comment))
            with open(path, 'w') as xml_catalog:
                xml_catalog.write(etree.tostring(tree, pretty_print=True,
                    xml_declaration=True, encoding="UTF-8"))

            logger.debug('Downloaded schema %s', schema)

        return True

    except IOError as err:
        msg = 'Failed to download schema %s' % schema
        if hasattr(err, 'code'):
            msg += '(error code %s)' % err.code
        logger.warn(msg)

        return False


def generate_catalog():
    """Generating an XML catalog for schemas used by eulxml"""
    logger.debug("Generating a new XML catalog")

    # if the catalog dir doesn't exist, create it
    if not os.path.isdir(XMLCATALOG_DIR):
        os.mkdir(XMLCATALOG_DIR)

    # new xml catalog to be populated with saved schemas
    catalog = Catalog()

    # comment string to be added to locally-saved schemas
    comment = 'Downloaded by eulxml %s on %s' % \
        (__version__, date.today().isoformat())

    for schema_uri in XSD_SCHEMAS:
        filename = os.path.basename(schema_uri)
        schema_path = os.path.join(XMLCATALOG_DIR, filename)
        saved = download_schema(schema_uri, schema_path, comment)
        if saved:
            # if download succeeded, add to our catalog.
            # - name is the schema identifier (uri)
            # - uri is the local path to load
            # NOTE: using path relative to catalog file
            catalog.uri_list.append(Uri(name=schema_uri, uri=filename))

    # if we have any uris in our catalog, write it out
    if catalog.uri_list:
        with open(XMLCATALOG_FILE, 'w') as xml_catalog:
            catalog.serializeDocument(xml_catalog, pretty=True)
