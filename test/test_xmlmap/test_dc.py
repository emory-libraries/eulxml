# file test_xmlmap/test_dc.py
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

import unittest

from eulxml.xmlmap  import load_xmlobject_from_string
from eulxml.xmlmap.dc import DublinCore
from testcore import main

class TestDc(unittest.TestCase):
    # massaged dublin core sample from an Emory ETD record (fields added to ensure every DC field is tested)
    FIXTURE = """<oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
  <dc:title>Feet in the Fire</dc:title>
  <dc:title>Social Change and Continuity among the Diola of Guinea-Bissau</dc:title>
  <dc:creator>Davidson, Joanna Helen</dc:creator>
  <dc:subject>Anthropology, Cultural</dc:subject>
  <dc:subject>History, African</dc:subject>
  <dc:subject>West Africa</dc:subject>
  <dc:subject>Lusophone Africa</dc:subject>
  <dc:subject>Agrarian change</dc:subject>
  <dc:subject>Ethnicity</dc:subject>
  <dc:subject>Religious change</dc:subject>
  <dc:subject>Conflict</dc:subject>
  <dc:subject>Environmental change</dc:subject>
  <dc:subject>Cultural boundaries</dc:subject>
  <dc:description>Diola villagers in Guinea-Bissau...</dc:description>
  <dc:contributor>Knauft, Bruce M</dc:contributor>
  <dc:contributor>Karp, Ivan</dc:contributor>
  <dc:contributor>Donham, Donald L. (UC Davis)</dc:contributor>
  <dc:date>2007-12-31</dc:date>
  <dc:type>Dissertation</dc:type>
  <dc:type>text</dc:type>
  <dc:format>application/pdf</dc:format>
  <dc:identifier>emory:13q9n</dc:identifier>
  <dc:identifier>http://pid.emory.edu/ark:/25593/13q9n</dc:identifier>
  <dc:source>none</dc:source>
  <dc:language>English</dc:language>
  <dc:coverage>Guinea-Bissau</dc:coverage>
  <dc:coverage>2004-2006</dc:coverage>
  <dc:relation>https://etd.library.emory.edu/</dc:relation>
  <dc:publisher>Emory University</dc:publisher>
  <dc:rights>Permission granted by the author.</dc:rights>
</oai_dc:dc>
"""

    def setUp(self):
        self.dc = load_xmlobject_from_string(self.FIXTURE, DublinCore)

    def testInit(self):
        self.assert_(isinstance(self.dc, DublinCore))

    def testFields(self):
        self.assertEqual(self.dc.title, "Feet in the Fire")
        self.assertEqual(self.dc.title_list[1], "Social Change and Continuity among the Diola of Guinea-Bissau")
        self.assertEqual(self.dc.creator, "Davidson, Joanna Helen")
        self.assertEqual(self.dc.creator_list[0], "Davidson, Joanna Helen")
        self.assertEqual(self.dc.subject, "Anthropology, Cultural")
        self.assertEqual(self.dc.subject_list[1], "History, African")
        self.assertEqual(self.dc.subject_list[4], "Agrarian change")
        self.assertEqual(self.dc.subject_list[-1], "Cultural boundaries")
        self.assertEqual(self.dc.description, "Diola villagers in Guinea-Bissau...")
        self.assertEqual(self.dc.description_list[0], "Diola villagers in Guinea-Bissau...")
        self.assertEqual(self.dc.contributor, "Knauft, Bruce M")
        self.assertEqual(self.dc.contributor_list[1], "Karp, Ivan")
        self.assertEqual(self.dc.contributor_list[2], "Donham, Donald L. (UC Davis)")
        self.assertEqual(self.dc.date, "2007-12-31")
        self.assertEqual(self.dc.date_list[0], "2007-12-31")
        self.assertEqual(self.dc.type, "Dissertation")
        self.assertEqual(self.dc.type_list[1], "text")
        self.assertEqual(self.dc.format, "application/pdf")
        self.assertEqual(self.dc.format_list[0], "application/pdf")
        self.assertEqual(self.dc.identifier, "emory:13q9n")
        self.assertEqual(self.dc.identifier_list[1], "http://pid.emory.edu/ark:/25593/13q9n")
        self.assertEqual(self.dc.source, "none")
        self.assertEqual(self.dc.source_list[0], "none")
        self.assertEqual(self.dc.language, "English")
        self.assertEqual(self.dc.language_list[0], "English")
        self.assertEqual(self.dc.coverage, "Guinea-Bissau")
        self.assertEqual(self.dc.coverage_list[1], "2004-2006")
        self.assertEqual(self.dc.relation, "https://etd.library.emory.edu/")
        self.assertEqual(self.dc.relation_list[0], "https://etd.library.emory.edu/")
        self.assertEqual(self.dc.publisher, "Emory University")
        self.assertEqual(self.dc.publisher_list[0], "Emory University")
        self.assertEqual(self.dc.rights, "Permission granted by the author.")
        self.assertEqual(self.dc.rights_list[0], "Permission granted by the author.")

        # elements should provide access to all DC fields
        self.assertEqual(self.dc.elements[0].name, 'title')
        self.assertEqual(self.dc.elements[0].value, 'Feet in the Fire')
        self.assertEqual(self.dc.elements[8].name, 'subject')
        self.assertEqual(self.dc.elements[8].value, 'Ethnicity')
        self.assertEqual(self.dc.elements[-1].name, 'rights')
        self.assertEqual(self.dc.elements[-1].value, 'Permission granted by the author.')

    def testTemplateInit(self):
        dc = DublinCore()
        dc_xml = dc.serialize()
        self.assert_('<oai_dc:dc ' in dc_xml)
        self.assert_('xmlns:dc="http://purl.org/dc/elements/1.1/"' in dc_xml)
        self.assert_('xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"' in dc_xml)

    def test_isvalid(self):
        self.assertTrue(self.dc.is_valid())
        
        invalid = """<oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
  <dc:title>Feet in the Fire</dc:title>
        <not_a_dc_field>bogus</not_a_dc_field>
        </oai_dc:dc>
        """
        invalid_dc = load_xmlobject_from_string(invalid, DublinCore)
        self.assertFalse(invalid_dc.is_valid())

    def test_dcmitypes(self):
        types = self.dc.dcmi_types
        self.assert_(isinstance(types, list))
        # check a few items in the list
        self.assert_('Collection' in types)
        self.assert_('Still Image' in types)
        self.assert_('Event' in types)
        self.assert_('Text' in types)

if __name__ == '__main__':
    main()
