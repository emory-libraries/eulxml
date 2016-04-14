"""Unit Test for Catalog.py. Tests for download of schemas and catalog generation"""
# file test_xmlmap/test_core.py
#
#   Copyright 2011 Emory University Libraries
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

#!/usr/bin/env python

from __future__ import unicode_literals
import os
import unittest
try:
    from unittest import skipIf
except ImportError:
    from unittest2 import skipIf
import glob
try:
    from urllib.request import urlretrieve
    from urllib.request import urlopen
except ImportError:
    from urllib import urlretrieve
    from urllib import urlopen
import shutil
from datetime import date
from eulxml import xmlmap, __version__
from lxml import etree
from eulxml.catalog import Uri, Catalog



class TestGenerateSchema(unittest.TestCase):
    """:class:`TestGenerateSchema` class for Catalog testing"""
    def setUp(self):
        self.path = 'eulxml/test_schemas'
        self.correct_schema = 'http://www.loc.gov/standards/mods/v3/mods-3-4.xsd'
        self.wrong_schema = 'http://www.loc.gov/standards/mods/v3/mods34.xsd'
        self.comment = 'Downloaded by eulxml %s on %s' % \
              (__version__, date.today().isoformat())
        # parseString wants a url. let's give it a proper one.
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

    def tearDown(self):
        if os.path.isdir('eulxml/test_schemas'):
            shutil.rmtree('eulxml/test_schemas')

    def test_download_xml_schemas(self):
        """Check if xsd schemas exist and download fresh copies """

        #do files already exist
        check_xsds = len(glob.glob(''.join([self.path, '*.xsd'])))
        self.assertEqual(0, check_xsds)

        #downloading the wrong schema
        response_wrong = urlopen(self.wrong_schema)
        expected, got = 404, response_wrong.getcode()
        self.assertEqual(expected, got)
        #downloading the right schemas

        response_correct = urlopen(self.correct_schema)
        expected, got = 200, response_correct.getcode()
        self.assertEqual(expected, got)
        filename = os.path.basename(self.correct_schema)
        schema_path = os.path.join(self.path, filename)
        urlretrieve(self.correct_schema, schema_path)
        tree = etree.parse(schema_path)

        # Does comment exist?
        schema_string_no_comment = etree.tostring(tree)
        self.assertFalse("by eulxml" in schema_string_no_comment)


        #Add comment and check if it is there now
        tree.getroot().append(etree.Comment(self.comment))
        with open(schema_path, 'w') as xml_catalog:
            xml_catalog.write(etree.tostring(tree, pretty_print=True,
                                             xml_declaration=True, encoding="UTF-8"))

            schema_string_with_comment = etree.tostring(tree)
            self.assertTrue("by eulxml" in schema_string_with_comment)
        #check if all files were downloaded
        self.assertEqual(1, len(glob.glob(''.join([self.path, '/*.xsd']))))




    def test_generate_xml_catalog(self):
        """Check if the catalog exists and import xml files into data files """

        #check if catalog already exists
        check_catalog = len(glob.glob(''.join([self.path, '/catalog.xml'])))
        self.assertEqual(0, check_catalog)

        #generate empty catalog xml object
        catalog = Catalog()

        #check elements of generated catalog
        self.assertEqual('catalog', catalog.ROOT_NAME)
        self.assertEqual('urn:oasis:names:tc:entity:xmlns:xml:catalog', catalog.ROOT_NS)
        self.assertEqual({'c': catalog.ROOT_NS}, catalog.ROOT_NAMESPACES)
        self.assertEqual(0, len(catalog.uri_list))

        filename = os.path.basename(self.correct_schema)
        catalog_path = os.path.join(self.path, 'catalog.xml')
        catalog.uri_list.append(Uri(name=self.correct_schema, uri=filename))
        # check correct name attribute
        self.assertEqual(self.correct_schema, catalog.uri_list[0].name)
        # check correct uri attribute
        self.assertEqual(filename, catalog.uri_list[0].uri)

        # check how many uris we have in catalog
        self.assertEqual(len(catalog.uri_list), 1)

        with open(catalog_path, 'wb') as xml_catalog:
            catalog.serializeDocument(xml_catalog, pretty=True)

        #check if catalog was generated
        check_catalog = len(glob.glob(''.join([self.path, '/catalog.xml'])))
        self.assertEqual(1, check_catalog)

