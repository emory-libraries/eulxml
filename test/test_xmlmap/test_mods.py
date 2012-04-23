# file test_xmlmap/test_mods.py
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

from eulxml.xmlmap import load_xmlobject_from_string, mods
from testcore import main

class TestMods(unittest.TestCase):
    # tests for MODS XmlObject

    FIXTURE = """<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
  <mods:titleInfo>
    <mods:title>A simple record</mods:title>
    <mods:subTitle> (for test purposes)</mods:subTitle>
  </mods:titleInfo>
  <mods:typeOfResource>text</mods:typeOfResource>
  <mods:note displayLabel="a general note" type="general">remember to...</mods:note>
  <mods:originInfo>
    <mods:dateCreated keyDate='yes'>2010-06-17</mods:dateCreated>
    <mods:publisher>Little, Brown</mods:publisher>
  </mods:originInfo>
  <mods:identifier type='uri'>http://so.me/uri</mods:identifier>
  <mods:name type="personal" authority="naf" ID="n82032703">
    <mods:namePart>Dawson, William Levi</mods:namePart>
    <mods:namePart type="date">1899-1990</mods:namePart>
    <mods:displayForm>William Levi Dawson (1899-1990)</mods:displayForm>
    <mods:affiliation>Tuskegee</mods:affiliation>
    <mods:role>
      <mods:roleTerm type="text" authority="marcrelator">Composer</mods:roleTerm>
    </mods:role>
  </mods:name>
  <mods:abstract>Dawson choir recordings</mods:abstract>
  <mods:accessCondition type="restrictions on access">Restricted</mods:accessCondition>
  <mods:relatedItem type="host">
    <mods:titleInfo>
      <mods:title>Emory University Archives</mods:title>
    </mods:titleInfo>
  <mods:identifier type="local_sourcecoll_id">eua</mods:identifier>
  </mods:relatedItem>
  <mods:location>
    <mods:physicalLocation>Atlanta</mods:physicalLocation>
    <mods:url>http://so.me/other/uri</mods:url>
  </mods:location>
  <mods:part>
    <mods:detail type="volume">
      <mods:number>II</mods:number>
    </mods:detail>
    <mods:extent unit="pages">
      <mods:start>5</mods:start>
      <mods:end>23</mods:end>
    </mods:extent>
  </mods:part>
</mods:mods>
"""
    invalid_xml = """<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
    <mods:titleInfo><mods:title invalid_attribute='oops'>An invalid record</mods:title></mods:titleInfo>
</mods:mods>
        """

    def setUp(self):
        super(TestMods, self).setUp()
        self.mods = load_xmlobject_from_string(self.FIXTURE, mods.MODS)

    def test_init_types(self):
        self.assert_(isinstance(self.mods, mods.MODS))
        self.assert_(isinstance(self.mods.note, mods.Note))
        self.assert_(isinstance(self.mods.origin_info, mods.OriginInfo))
        self.assert_(isinstance(self.mods.origin_info.created[0], mods.DateCreated))
        self.assert_(isinstance(self.mods.identifiers[0], mods.Identifier))
        self.assert_(isinstance(self.mods.name, mods.Name))
        self.assert_(isinstance(self.mods.name.name_parts[0], mods.NamePart))
        self.assert_(isinstance(self.mods.name.roles[0], mods.Role))
        self.assert_(isinstance(self.mods.access_conditions[0], mods.AccessCondition))
        self.assert_(isinstance(self.mods.related_items[0], mods.RelatedItem))
        self.assert_(isinstance(self.mods.title_info, mods.TitleInfo))
        self.assert_(isinstance(self.mods.abstract, mods.Abstract))
        self.assert_(isinstance(self.mods.parts[0], mods.Part))
        self.assert_(isinstance(self.mods.parts[0].details[0], mods.PartDetail))
        self.assert_(isinstance(self.mods.parts[0].extent, mods.PartExtent))
        self.assert_(isinstance(self.mods.locations[0], mods.Location))

    def test_fields(self):
        self.assertEqual('A simple record', self.mods.title)
        self.assertEqual('text', self.mods.resource_type)
        self.assertEqual('a general note', self.mods.note.label)
        self.assertEqual('general', self.mods.note.type)
        self.assertEqual(u'remember to...', unicode(self.mods.note))
        self.assertEqual('remember to...', self.mods.note.text)
        self.assertEqual(u'2010-06-17', unicode(self.mods.origin_info.created[0]))
        self.assertEqual('2010-06-17', self.mods.origin_info.created[0].date)
        self.assertEqual(True, self.mods.origin_info.created[0].key_date)
        self.assertEqual('Little, Brown', self.mods.origin_info.publisher)
        self.assertEqual(u'http://so.me/uri', self.mods.identifiers[0].text)
        self.assertEqual(u'uri', self.mods.identifiers[0].type)
        self.assertEqual(u'Dawson choir recordings', self.mods.abstract.text)
        # name fields
        self.assertEqual(u'personal', self.mods.name.type)
        self.assertEqual(u'naf', self.mods.name.authority)
        self.assertEqual(u'n82032703', self.mods.name.id)
        self.assertEqual(u'Dawson, William Levi', self.mods.name.name_parts[0].text)
        self.assertEqual(u'1899-1990', self.mods.name.name_parts[1].text)
        self.assertEqual(u'date', self.mods.name.name_parts[1].type)
        self.assertEqual(u'William Levi Dawson (1899-1990)', self.mods.name.display_form)
        self.assertEqual(u'Tuskegee', self.mods.name.affiliation)
        self.assertEqual(u'text', self.mods.name.roles[0].type)
        self.assertEqual(u'marcrelator', self.mods.name.roles[0].authority)
        self.assertEqual(u'Composer', self.mods.name.roles[0].text)
        # access condition
        self.assertEqual(u'restrictions on access', self.mods.access_conditions[0].type)
        self.assertEqual(u'Restricted', self.mods.access_conditions[0].text)
        # related item
        self.assertEqual(u'host', self.mods.related_items[0].type)
        self.assertEqual(u'Emory University Archives', self.mods.related_items[0].title)
        self.assertEqual(u'local_sourcecoll_id', self.mods.related_items[0].identifiers[0].type)
        self.assertEqual(u'eua', self.mods.related_items[0].identifiers[0].text)
        # titleInfo subfields
        self.assertEqual('A simple record', self.mods.title_info.title)
        self.assertEqual(' (for test purposes)', self.mods.title_info.subtitle)
        # part
        self.assertEqual('volume', self.mods.parts[0].details[0].type)
        self.assertEqual('II', self.mods.parts[0].details[0].number)
        self.assertEqual('pages', self.mods.parts[0].extent.unit)
        self.assertEqual('5', self.mods.parts[0].extent.start)
        self.assertEqual('23', self.mods.parts[0].extent.end)
        # location
        self.assertEqual('http://so.me/other/uri', self.mods.locations[0].url)
        self.assertEqual('Atlanta', self.mods.locations[0].physical)

    def test_create_mods(self):
        # test creating MODS from scratch - ensure sub-xmlobject definitions are correct
        # and produce schema-valid MODS
        mymods = mods.MODS()
        mymods.create_title_info()
        # titleInfo subfields
        mymods.title_info.non_sort = 'A '
        mymods.title_info.title = 'Record'
        mymods.title_info.subtitle = ': for testing'
        mymods.title_info.part_number = '1'
        mymods.title_info.part_name = 'first installment'
        mymods.resource_type = 'text'
        mymods.create_name()
        mymods.name.type = 'personal'
        mymods.name.authority = 'local'
        mymods.name.name_parts.extend([mods.NamePart(type='family', text='Schmoe'),
                                    mods.NamePart(type='given', text='Joe')])
        mymods.name.roles.append(mods.Role(type='text', authority='local',
                                        text='Test Subject'))
        mymods.create_abstract()
        mymods.abstract.text = 'A testing record with made up content.'
        mymods.create_note()
        mymods.note.type = 'general'
        mymods.note.text = 'general note'
        mymods.create_origin_info()
        mymods.origin_info.created.append(mods.DateCreated(date='2001-10-02'))
        mymods.origin_info.issued.append(mods.DateIssued(date='2001-12-01'))
        mymods.create_record_info()
        mymods.record_info.record_id = 'id:1'
        mymods.identifiers.extend([mods.Identifier(type='uri', text='http://ur.l'),
                                 mods.Identifier(type='local', text='332')])
        mymods.access_conditions.extend([mods.AccessCondition(type='restriction', text='unavailable'),
                                       mods.AccessCondition(type='use', text='Tuesdays only')])
        mymods.related_items.extend([mods.RelatedItem(type='host', title='EU Archives'),
                                   mods.RelatedItem(type='isReferencedBy', title='Finding Aid'),])
        mymods.subjects.extend([mods.Subject(authority='keyword', topic='automated testing'),
                                mods.Subject(authority='keyword', topic='test records')])
        mymods.parts.append(mods.Part())
        mymods.parts[0].details.extend([mods.PartDetail(type='volume', number='90'),
                                        mods.PartDetail(type='issue', number='2')])
        mymods.parts[0].create_extent()
        mymods.parts[0].extent.unit = 'pages'
        mymods.parts[0].extent.start = '339'
        mymods.parts[0].extent.end = '361'
        xml = mymods.serialize(pretty=True)
        self.assert_('<mods:mods ' in xml)
        self.assert_('xmlns:mods="http://www.loc.gov/mods/v3"' in xml)

        self.assertTrue(mymods.is_valid(), "MODS created from scratch should be schema-valid")

    def test_isvalid(self):
        # if additions to MODS test fixture cause validation errors, uncomment the next 2 lines to debug
        #self.mods.is_valid()
        #print self.mods.validation_errors()
        self.assertTrue(self.mods.is_valid())        
        invalid_mods = load_xmlobject_from_string(self.invalid_xml, mods.MODS)
        self.assertFalse(invalid_mods.is_valid())

class TestModsTypedNote(unittest.TestCase):
    # node fields tested in main mods test case; testing custom is_empty logic here

    def setUp(self):
        super(TestModsTypedNote, self).setUp()
        self.note = mods.TypedNote()
        self.note.type = 'general'

    def test_is_empty(self):
        # initial note object should be considered empty (type only)
        self.assertTrue(self.note.is_empty())

    def test_is_empty__extra_attribute(self):
        # set an attribute besides type
        self.note.label = "Note"        
        self.assertFalse(self.note.is_empty())

    def test_is_empty_text(self):
        # set text value
        self.note.text = 'here is some general info'
        self.assertFalse(self.note.is_empty())

class TestModsDate(unittest.TestCase):
    # node fields tested in main mods test case; testing custom is_empty logic here

    def setUp(self):
        super(TestModsDate, self).setUp()
        self.date = mods.DateCreated() 

    def test_is_empty(self):
        # starting fixture should be considered empty (no date)
        self.assertTrue(self.date.is_empty())

    def test_is_empty_with_attributes(self):
        # should be empty with attributes but no date value
        self.date.keydate = True
        self.assertTrue(self.date.is_empty())

    def test_is_empty_date_value(self):
        # set date value
        self.date.date = '1066'
        self.assertFalse(self.date.is_empty())

class TestModsOriginInfo(unittest.TestCase):
    # node fields tested in main mods test case; testing custom is_empty logic here

    def setUp(self):
        super(TestModsOriginInfo, self).setUp()
        self.origin_info = mods.OriginInfo()

    def test_is_empty(self):
        # starting object should be considered empty (no date elements at all)
        self.assertTrue(self.origin_info.is_empty())

    def test_is_empty_with_empty_dates(self):
        self.origin_info.created.append(mods.DateCreated())
        self.assertTrue(self.origin_info.is_empty())
        self.origin_info.issued.append(mods.DateIssued())
        self.assertTrue(self.origin_info.is_empty())

    def test_is_empty_date_values(self):
        self.origin_info.created.append(mods.DateCreated(date='300'))
        self.assertFalse(self.origin_info.is_empty())
        self.origin_info.issued.append(mods.DateIssued(date='450'))
        self.assertFalse(self.origin_info.is_empty())

    def test_not_empty_with_publisher(self):
        self.origin_info.publisher = 'MacMillan'
        self.assertFalse(self.origin_info.is_empty())

class TestModsPart(unittest.TestCase):

    def setUp(self):
        super(TestModsPart, self).setUp()
        self.part = mods.Part()

    def test_is_empty(self):
        # new, no values - empty
        self.assertTrue(self.part.is_empty())

        # with empty extent - still empty
        self.part.create_extent()
        self.assertTrue(self.part.is_empty())

        # type value - not empty
        self.part.type = 'something'
        self.assertFalse(self.part.is_empty())


class TestTitleInfo(unittest.TestCase):

    def setUp(self):
        super(TestTitleInfo, self).setUp()
        self.titleinfo = mods.TitleInfo()

    def test_is_empty(self):
        # new, no values - empty
        self.assertTrue(self.titleinfo.is_empty())

        # with empty field - still empty
        self.titleinfo.title = ''
        self.assertTrue(self.titleinfo.is_empty())
        
        # actual value - not empty
        self.titleinfo.title = 'This a Test'
        self.assertFalse(self.titleinfo.is_empty())


if __name__ == '__main__':
    main()
