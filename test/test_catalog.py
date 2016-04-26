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
import tempfile
try:
    from unittest import skipIf
except ImportError:
    from unittest2 import skipIf
import glob
import shutil
from datetime import date
import requests
from eulxml import __version__
from lxml import etree
from eulxml.catalog import download_schema, generate_catalog, XSD_SCHEMAS



class TestGenerateSchema(unittest.TestCase):
    """:class:`TestGenerateSchema` class for Catalog testing"""
    def setUp(self):
        self.correct_schema = 'http://www.loc.gov/standards/mods/v3/mods-3-4.xsd'
        self.wrong_schema = 'http://www.loc.gov/standards/mods/v3/mods34.xsd'
        self.comment = 'Downloaded by eulxml %s on %s' % \
              (__version__, date.today().isoformat())
        # parseString wants a url. let's give it a proper one.
        self.path = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path)

    def test_download_xml_schemas(self):
        """Check if xsd schemas exist and download fresh copies """
        filename = os.path.basename(self.correct_schema)
        schema_path = os.path.join(self.path, filename)
        #do files already exist
        check_xsds = len(glob.glob(''.join([self.path, '*.xsd'])))
        self.assertEqual(0, check_xsds)

        #downloading the wrong schema
        response_wrong = download_schema(self.wrong_schema, schema_path, comment=None)
        self.assertFalse(response_wrong)

        #downloading the right schemas
        response_correct = download_schema(self.correct_schema, schema_path, comment=None)
        self.assertTrue(response_correct)

        tree = etree.parse(schema_path)

        # Does comment exist?
        schema_string_no_comment = etree.tostring(tree)
        self.assertFalse(b'by eulxml' in schema_string_no_comment)


        #Add comment and check if it is there now
        download_schema(self.correct_schema, schema_path, comment=self.comment)
        tree = etree.parse(schema_path)
        schema_string_with_comment = etree.tostring(tree)
        self.assertTrue(b'by eulxml' in schema_string_with_comment)

        #check if all files were downloaded
        self.assertEqual(1, len(glob.glob(''.join([self.path, '/*.xsd']))))


    def test_generate_xml_catalog(self):
        """Check if the catalog exists and import xml files into data files """

        #check if catalog already exists
        check_catalog = len(glob.glob(''.join([self.path, '/catalog.xml'])))
        self.assertEqual(0, check_catalog)
        catalog_file = os.path.join(self.path, 'catalog.xml')
        filename = os.path.basename(self.correct_schema)
        #generate empty catalog xml object
        catalog = generate_catalog(xsd_schemas=[self.correct_schema], xmlcatalog_dir=self.path, xmlcatalog_file=catalog_file)

        #check if catalog was generated
        check_catalog = len(glob.glob(''.join([self.path, '/catalog.xml'])))
        self.assertEqual(1, check_catalog)


        #check elements of generated catalog
        self.assertEqual('catalog', catalog.ROOT_NAME)
        self.assertEqual('urn:oasis:names:tc:entity:xmlns:xml:catalog', catalog.ROOT_NS)
        self.assertEqual({'c': catalog.ROOT_NS}, catalog.ROOT_NAMESPACES)
        self.assertEqual(1, len(catalog.uri_list))

        # check correct name attribute
        self.assertEqual(self.correct_schema, catalog.uri_list[0].name)
        # check correct uri attribute
        self.assertEqual(filename, catalog.uri_list[0].uri)

        # check how many uris we have in catalog
        self.assertEqual(len(catalog.uri_list), 1)

