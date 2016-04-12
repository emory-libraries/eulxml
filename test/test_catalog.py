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
import tempfile
import glob
import urllib
import time
from eulxml import xmlmap
from lxml import etree



class TestGenerateSchema(unittest.TestCase):  
    def setUp(self):
        # parseString wants a url. let's give it a proper one.
        XSD_SCHEMAS = ['http://www.loc.gov/standards/mods/v3/mods-3-4.xsd',
                       'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
                       'http://www.loc.gov/standards/xlink/xlink.xsd',
                       'http://www.loc.gov/standards/premis/premis.xsd',
                       'http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd',
                       'http://www.tei-c.org/release/xml/tei/custom/schema/xsd/tei_all.xsd']
        if not os.path.exists('tmp2'):
            os.makedirs('eulxml/tmp2')

    def tearDown(self):
        if os.path.exists('eulxml/tmp2'):
            os.rmdir('eulxml/tmp2')

    def test_download_xmlschemas(self):
        """Check if the catalog exists and import xml files into data files """


    def test_generate_xml_catalog(self):
        """Check if the catalog exists and import xml files into data files """