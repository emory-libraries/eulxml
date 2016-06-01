# file eulxml/catalog.py
#
#   Copyright 2016 Emory University Libraries
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

'''
Logic for downloading local copies of schemas and generating an
`XML catalog <http://lxml.de/resolvers.html#xml-catalogs`_ for use in
resolving schemas locally instead of downloading them every time validation
is required.

Catalog generation is available via the setup.py custom command xmlcatalog,
and a generated catalog and corresponding schema files should be included
in packaged releases of eulxml.

For more information about setting up and testing XML catalogs, see the
`libxml2 documentation <http://xmlsoft.org/catalog.html>`_.
'''

import os
import logging
from datetime import date
from lxml import etree
import sys

from eulxml import xmlmap, __version__, XMLCATALOG_DIR, XMLCATALOG_FILE

# requests is an optional dependency, handle gracefully if not present
try:
    import requests
except ImportError:
    requests = None


logger = logging.getLogger(__name__)

# message to display if requests is not available
req_requests_msg = 'Please install requests to download schemas ' + \
                   '(pip install requests)\n'


XSD_SCHEMAS = [
    'http://www.loc.gov/standards/mods/mods.xsd',
    'http://www.loc.gov/standards/mods/v3/mods-3-4.xsd',
    'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
    'http://www.loc.gov/standards/xlink/xlink.xsd',
    'http://www.loc.gov/standards/premis/premis.xsd',
    'http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd',
    'http://www.tei-c.org/release/xml/tei/custom/schema/xsd/tei_all.xsd',
    'http://www.history.ncdcr.gov/SHRAB/ar/emailpreservation/mail-account/mail-account.xsd',
    'http://www.loc.gov/ead/ead.xsd'
]
# , 'http://www.archives.ncdcr.gov/mail-account.xsd'


class Uri(xmlmap.XmlObject):
    """:class:`xmlmap.XmlObject` class for Catalog URIs"""
    ROOT_NAME = 'uri'
    ROOT_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
    #: name, i.e. schema URI
    name = xmlmap.StringField('@name')
    #: uri, i.e. path to load the schema locally
    uri = xmlmap.StringField('@uri')


class Catalog(xmlmap.XmlObject):
    """:class:`xmlmap.XmlObject` class to for generating XML Catalogs"""
    ROOT_NAME = 'catalog'
    ROOT_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"
    ROOT_NAMESPACES = {'c': ROOT_NS}
    #: list of uris, as instance of :class:`Uri`
    uri_list = xmlmap.NodeListField('c:uri', Uri)


def download_schema(uri, path, comment=None):
    """Download a schema from a specified URI and save it locally.

    :param uri: url where the schema should be downloaded
    :param path: local file path where the schema should be saved
    :param comment: optional comment; if specified, will be added to
        the downloaded schema
    :returns: true on success, false if there was an error and the
        schema failed to download
    """
    # if requests isn't available, warn and bail out
    if requests is None:
        sys.stderr.write(req_requests_msg)
        return

    # short-hand name of the schema, based on uri
    schema = os.path.basename(uri)
    try:

        req = requests.get(uri, stream=True)
        req.raise_for_status()
        with open(path, 'wb') as schema_download:
            for chunk in req.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    schema_download.write(chunk)
        # if a comment is specified, add it to the locally saved schema
        if comment is not None:
            tree = etree.parse(path)
            tree.getroot().append(etree.Comment(comment))
            with open(path, 'wb') as xml_catalog:
                xml_catalog.write(etree.tostring(tree, pretty_print=True,
                    xml_declaration=True, encoding="UTF-8"))
            logger.debug('Downloaded schema %s', schema)

        return True

    except requests.exceptions.HTTPError as err:
        msg = 'Failed to download schema %s' % schema
        msg += '(error codes %s)' % err.response.status_code
        logger.warn(msg)

        return False


def generate_catalog(xsd_schemas=None, xmlcatalog_dir=None, xmlcatalog_file=None):
    """Generating an XML catalog for use in resolving schemas

    Creates the XML Catalog directory if it doesn't already exist.
    Uses :meth:`download_schema` to save local copies of schemas,
    adding a comment indicating the date downloaded by eulxml.

    Generates a new catalog.xml file, with entries for all schemas
    that downloaded successfully.  If no schemas downloaded, the catalog
    is not generated.

    .. Note::

        Currently this method overwites any existing schema and catalog
        files, without checking if they are present or need to be
        updated.

    """
    # if requests isn't available, warn and bail out
    if requests is None:
        sys.stderr.write(req_requests_msg)
        return

    logger.debug("Generating a new XML catalog")
    if xsd_schemas is None:
        xsd_schemas = XSD_SCHEMAS

    if xmlcatalog_file is None:
        xmlcatalog_file = XMLCATALOG_FILE

    if xmlcatalog_dir is None:
        xmlcatalog_dir = XMLCATALOG_DIR
    # if the catalog dir doesn't exist, create it
    if not os.path.isdir(xmlcatalog_dir):
        os.mkdir(xmlcatalog_dir)

    # new xml catalog to be populated with saved schemas
    catalog = Catalog()

    # comment string to be added to locally-saved schemas
    comment = 'Downloaded by eulxml %s on %s' % \
        (__version__, date.today().isoformat())

    for schema_uri in xsd_schemas:
        filename = os.path.basename(schema_uri)
        schema_path = os.path.join(xmlcatalog_dir, filename)
        saved = download_schema(schema_uri, schema_path, comment)
        if saved:
            # if download succeeded, add to our catalog.
            # - name is the schema identifier (uri)
            # - uri is the local path to load
            # NOTE: using path relative to catalog file
            catalog.uri_list.append(Uri(name=schema_uri, uri=filename))

    # if we have any uris in our catalog, write it out
    if catalog.uri_list:
        with open(xmlcatalog_file, 'wb') as xml_catalog:
            catalog.serializeDocument(xml_catalog, pretty=True)
    return catalog
