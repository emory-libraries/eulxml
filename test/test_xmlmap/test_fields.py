# file test_xmlmap/test_fields.py
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

from datetime import datetime
import tempfile
import unittest

import eulxml.xmlmap.core as xmlmap
from testcore import main

class TestFields(unittest.TestCase):
    FIXTURE_TEXT = '''
        <foo id='a' xmlns:ex='http://example.com/'>
            <bar>
                <baz>42</baz>
            </bar>
            <bar>
                <baz>13</baz>
            </bar>
            <empty_field/>
            <boolean>
                    <text1>yes</text1>
                    <text2>no</text2>
                    <num1>1</num1>
                    <num2>0</num2>
            </boolean>
            <spacey>           this text
        needs to be
                normalized
            </spacey>
            <date>2010-01-03T02:13:44</date>
            <date>2010-01-03T02:13:44.003</date>
        </foo>
    '''

    namespaces = {'ex' : 'http://example.com/'}

    def setUp(self):
        # parseString wants a url. let's give it a proper one.
        url = '%s#%s.%s' % (__file__, self.__class__.__name__, 'FIXTURE_TEXT')

        self.fixture = xmlmap.parseString(self.FIXTURE_TEXT, url)
        
        self.rel_url = '%s#%s' % (__file__, self.__class__.__name__)

    def _empty_fixture(self):
        return xmlmap.parseString('<root/>', self.rel_url)

    def testInvalidXpath(self):
        self.assertRaises(Exception, xmlmap.StringField, '["')
        
    def testNodeField(self):
        class TestSubobject(xmlmap.XmlObject):
            ROOT_NAME = 'bar'
            val = xmlmap.StringField('baz')

        class TestObject(xmlmap.XmlObject):
            child = xmlmap.NodeField('bar[1]', TestSubobject, required=True)
            missing = xmlmap.NodeField('missing', TestSubobject)

        obj = TestObject(self.fixture)
        self.assertEqual(obj.child.val, '42')
        self.assertEqual(obj.missing, None)
        # undefined if >1 matched nodes

        # test set
        obj.child = TestSubobject(val='144')
        self.assertEqual(obj.child.val, '144')

        # check required
        self.assertTrue(obj._fields['child'].required)

        # test create_foo functionality
        class CreateTestObject(xmlmap.XmlObject):
            missing = xmlmap.NodeField('missing', TestSubobject)
        obj = CreateTestObject(self.fixture)
        self.assert_(obj.missing is None)
        obj.create_missing()
        self.assert_(isinstance(obj.missing, TestSubobject))

        # test del
        del obj.missing
        self.assertEqual(obj.missing, None)

        # test DEPRECATED instantiate on get hack
        class GetTestObject(xmlmap.XmlObject):
            missing = xmlmap.NodeField('missing', TestSubobject, instantiate_on_get=True)
        obj = GetTestObject(self.fixture)
        self.assert_(isinstance(obj.missing, TestSubobject),
            "non-existent nodefield is created on get when 'instantiate_on_get' flag is set")

    def testNodeListField(self):
        class TestSubobject(xmlmap.XmlObject):
            val = xmlmap.IntegerField('baz')

        class TestObject(xmlmap.XmlObject):
            children = xmlmap.NodeListField('bar', TestSubobject)
            missing = xmlmap.NodeListField('missing', TestSubobject, required=False)

        obj = TestObject(self.fixture)
        child_vals = [ child.val for child in obj.children ]
        self.assertEqual(child_vals, [42, 13])
        self.assertEqual(obj.missing, [])

        # check required
        self.assertFalse(obj._fields['missing'].required)

        # is_empty
        self.assertFalse(obj.children.is_empty())
        del obj.children
        self.assertTrue(obj.children.is_empty())


    def testStringField(self):
        class TestObject(xmlmap.XmlObject):
            val = xmlmap.StringField('bar[1]/baz', required=True)
            empty = xmlmap.StringField('empty_field', required=False)
            missing = xmlmap.StringField('missing')
            missing_ns = xmlmap.StringField('ex:missing')
            missing_att = xmlmap.StringField('@missing')
            missing_att_ns = xmlmap.StringField('@ex:missing')
            sub_missing = xmlmap.StringField('bar[1]/missing')
            multilevel_missing = xmlmap.StringField('missing_parent/missing_child')
            mixed = xmlmap.StringField('bar[1]')
            id = xmlmap.StringField('@id')
            spacey = xmlmap.StringField('spacey')
            normal_spacey = xmlmap.StringField('spacey', normalize=True)

        obj = TestObject(self.fixture)
        self.assertEqual(obj.val, '42')
        self.assertEqual(obj.missing, None)
        # undefined if >1 matched nodes

        # access normalized and non-normalized versions of string field
        self.assertNotEqual("this text needs to be normalized", obj.spacey)
        self.assertEqual("this text needs to be normalized", obj.normal_spacey)

        # set an existing string value
        obj.val = "forty-two"
        # check that new value is set in the node
        self.assertEqual(obj.node.xpath('string(bar[1]/baz)'), "forty-two")
        # check that new value is accessible via descriptor        
        self.assertEqual(obj.val, 'forty-two')

        # set an attribute
        obj.id = 'z'
        # check that new value is set in the node
        self.assertEqual(obj.node.xpath('string(@id)'), "z")
        # check that new value is accessible via descriptor
        self.assertEqual(obj.id, 'z')

        # set value in an empty node
        obj.empty = "full"
        self.assertEqual(obj.node.xpath('string(empty_field)'), "full")
        # check that new value is accessible via descriptor
        self.assertEqual(obj.empty, 'full')

        # set missing fields
        obj.missing = 'not here'
        self.assertEqual(obj.node.xpath('string(missing)'), 'not here')
        # with ns
        obj.missing_ns = 'over there'
        self.assertEqual(obj.node.xpath('string(ex:missing)', namespaces=self.namespaces),
                    'over there')
        # in attrib
        obj.missing_att = 'out to pasture'
        self.assertEqual(obj.node.xpath('string(@missing)'), 'out to pasture')
        # in attrib with ns
        obj.missing_att_ns = "can't find me!"
        self.assertEqual(obj.node.xpath('string(@ex:missing)',
                        namespaces=self.namespaces), "can't find me!")
        # in subelement
        obj.sub_missing = 'pining (for the fjords)'
        self.assertEqual(obj.node.xpath('string(bar/missing)'), 'pining (for the fjords)')

        # in subelement which is itself missing
        obj.multilevel_missing = 'so, so gone'
        self.assertEqual(obj.node.xpath('string(missing_parent/missing_child)'), 'so, so gone')

        # attempting to set a node that contains non-text nodes - error
        self.assertRaises(Exception, obj.__setattr__, "mixed", "whoops")

        # set an existing string value to None
        # - attribute
        obj.id = None
        # check that attribute was removed from the xml
        self.assertEqual(0, obj.node.xpath('count(@id)'))
        self.assertEqual(None, obj.id)
        # - element
        obj.val = None
        # check that node is removed from the xml
        self.assertEqual(0, obj.node.xpath('count(bar[1]/baz)'))
        self.assertEqual(None, obj.val)

        # set to empty string - should store empty string and NOT remove the node
        # - attribute
        obj.id = ''
        # check that attribute was removed from the xml
        self.assertEqual('', obj.node.xpath('string(@id)'))
        self.assertEqual('', obj.id)
        # - element
        obj.val = ''
        # check that node is removed from the xml
        self.assertEqual('', obj.node.xpath('string(bar[1]/baz)'))
        self.assertEqual('', obj.val)

        # delete
        delattr(obj, 'spacey')
        # check that node is removed from the xml
        self.assertEqual(0, obj.node.xpath('count(spacey)'))
        self.assertEqual(None, obj.spacey)

        # check required
        self.assertTrue(obj._fields['val'].required)
        self.assertFalse(obj._fields['empty'].required)
        self.assertEqual(None, obj._fields['missing'].required)

    def testTextNode(self):
        # special case for text()
        class TextObject(xmlmap.XmlObject):
            text_node = xmlmap.StringField('text()')
            nested_text =  xmlmap.StringField('nest[@type="feather"]/text()')
            missing_text = xmlmap.StringField('missing[@type="foo"]/bar/text()')
            m_nested_attr = xmlmap.StringField('missing[@type="foo"]/bar/@label')
            m_nested_text = xmlmap.StringField('missing[@type="foo"]/baz')
            nested_child_pred = xmlmap.StringField('missing[@type="foo"][baz="bah"]/txt')
        # parseString wants a url. let's give it a proper one.
        url = '%s#%s.%s' % (__file__, self.__class__.__name__, 'TEXT_XML_FIXTURES')
        xml = '''<text>some text<nest type='feather'>robin</nest></text>'''
        obj = TextObject(xmlmap.parseString(xml, url))

        self.assertEqual('some text', obj.text_node)
        
        # set text node
        obj.text_node = 'la'
        self.assertEqual('la', obj.node.xpath('string(text())'))
        self.assertEqual('la', obj.text_node)
        # set to empty string
        obj.text_node = ''
        self.assertEqual('', obj.node.xpath('string(text())'))
        self.assertEqual('', obj.text_node)
        # set to value then set to None - text should be cleared out
        obj.text_node = 'la'
        obj.text_node = None
        self.assertEqual('', obj.node.xpath('string(text())'))
        self.assertEqual('', obj.text_node)

        self.assertEqual('robin', obj.nested_text)

        # create parent of a text node
        obj.missing_text = 'tra'
        self.assertEqual('tra', obj.node.xpath('string(missing/bar/text())'))
        self.assertEqual('tra', obj.missing_text)

    def testStringListField(self):
        class TestObject(xmlmap.XmlObject):
            vals = xmlmap.StringListField('bar/baz', required=True)
            missing = xmlmap.StringListField('missing')
            spacey = xmlmap.StringListField('spacey', normalize=True)

        obj = TestObject(self.fixture)
        self.assertEqual(obj.vals, ['42', '13'])
        self.assertEqual(obj.missing, [])

        # access normalized string list field
        self.assertEqual("this text needs to be normalized", obj.spacey[0])

        # delete list field
        delattr(obj, 'spacey')
        # check that node is removed from the xml
        self.assertEqual(0, obj.node.xpath('count(spacey)'))
        self.assertEqual([], obj.spacey)

        # check required
        self.assertTrue(obj._fields['vals'].required)
        

    def testIntegerField(self):
        class TestObject(xmlmap.XmlObject):
            val = xmlmap.IntegerField('bar[2]/baz', required=True)
            count = xmlmap.IntegerField('count(//bar)')
            missing = xmlmap.IntegerField('missing')
            nan = xmlmap.IntegerField('@id')

        obj = TestObject(self.fixture)
        self.assertEqual(obj.val, 13)
        self.assertEqual(obj.count, 2)
        self.assertEqual(obj.missing, None)
        self.assertEqual(obj.nan, None)
        # undefined if >1 matched nodes

        # set an integer value
        obj.val = 14
        # check that new value is set in the node
        self.assertEqual(obj.node.xpath('number(bar[2]/baz)'), 14)
        # check that new value is accessible via descriptor
        self.assertEqual(obj.val, 14)

        # check required
        self.assertTrue(obj._fields['val'].required)

    def testIntegerListField(self):
        class TestObject(xmlmap.XmlObject):
            vals = xmlmap.IntegerListField('bar/baz')
            missing = xmlmap.IntegerListField('missing', required=False)

        obj = TestObject(self.fixture)
        self.assertEqual(obj.vals, [42, 13])
        self.assertEqual(obj.missing, [])

        # check required
        self.assertFalse(obj._fields['missing'].required)

    def testItemField(self):
        class TestObject(xmlmap.XmlObject):
            letter = xmlmap.ItemField('substring(bar/baz, 1, 1)')
            missing = xmlmap.ItemField('missing', required=False)

        obj = TestObject(self.fixture)
        self.assertEqual(obj.letter, '4')
        self.assertEqual(obj.missing, None)

        # check required
        self.assertFalse(obj._fields['missing'].required)

    def testBooleanField(self):        
        class TestObject(xmlmap.XmlObject):
            txt_bool1 = xmlmap.SimpleBooleanField('boolean/text1', 'yes', 'no', required=False)
            txt_bool2 = xmlmap.SimpleBooleanField('boolean/text2', 'yes', 'no')
            num_bool1 = xmlmap.SimpleBooleanField('boolean/num1', 1, 0)
            num_bool2 = xmlmap.SimpleBooleanField('boolean/num2', 1, 0)
            opt_elem_bool = xmlmap.SimpleBooleanField('boolean/opt', 'yes', None)
            opt_attr_bool = xmlmap.SimpleBooleanField('boolean/@opt', 'yes', None)

        #obj = TestObject(self.fixture.documentElement)
        obj = TestObject(self.fixture)
        self.assertEqual(obj.txt_bool1, True)
        self.assertEqual(obj.txt_bool2, False)
        self.assertEqual(obj.num_bool1, True)
        self.assertEqual(obj.num_bool2, False)
        self.assertEqual(obj.opt_elem_bool, False)
        self.assertEqual(obj.opt_attr_bool, False)

        # set text boolean
        obj.txt_bool1 = False
        # check that new value is set in the node
        self.assertEqual(obj.node.xpath('string(boolean/text1)'), 'no')
        # check that new value is accessible via descriptor
        self.assertEqual(obj.txt_bool1, False)

        # set numeric boolean
        obj.num_bool1 = False
        # check for new new value in the node and via descriptor
        self.assertEqual(obj.node.xpath('number(boolean/num1)'), 0)
        self.assertEqual(obj.num_bool1, False)

        # set optional element boolean
        obj.opt_elem_bool = True
        self.assertEqual(obj.node.xpath('string(boolean/opt)'), 'yes')
        self.assertEqual(obj.opt_elem_bool, True)
        obj.opt_elem_bool = False
        self.assertEqual(obj.node.xpath('count(boolean/opt)'), 0)
        self.assertEqual(obj.opt_elem_bool, False)

        # set optional attribute boolean
        obj.opt_attr_bool = True
        self.assertEqual(obj.node.xpath('string(boolean/@opt)'), 'yes')
        self.assertEqual(obj.opt_attr_bool, True)
        obj.opt_attr_bool = False
        self.assertEqual(obj.node.xpath('count(boolean/@opt)'), 0)
        self.assertEqual(obj.opt_attr_bool, False)

        # check required
        self.assertFalse(obj._fields['txt_bool1'].required)


    # FIXME: DateField and DateListField are hacked together. Until we
    #   work up some proper parsing and good testing for them, they should
    #   be considered untested and undocumented features.

    
    def testDateTimeField(self):        
        class TestObject(xmlmap.XmlObject):
            date = xmlmap.DateTimeField('date')
            dates = xmlmap.DateTimeListField('date')

        obj = TestObject(self.fixture)
        # fields should be datetime objects
        self.assert_(isinstance(obj.date, datetime))
        self.assert_(isinstance(obj.dates[1], datetime))
        # inspect date parsing
        self.assertEqual(2010, obj.date.year)
        self.assertEqual(1, obj.date.month)
        self.assertEqual(3, obj.date.day)
        self.assertEqual(2, obj.date.hour)
        self.assertEqual(13, obj.date.minute)
        self.assertEqual(44, obj.date.second)
        # microsecond date parsing
        self.assertEqual(3000, obj.dates[1].microsecond)

        # set value via new datetime object
        today = datetime.today()
        obj.date = today
        self.assertEqual(obj.node.xpath('string(date)'), today.isoformat())


    def testFormattedDateTimeField(self):
        class TestObject(xmlmap.XmlObject):
            date = xmlmap.DateTimeField('date', format='%Y-%m-%dT%H:%M:%S')
            dates = xmlmap.DateTimeListField('date', format='%Y-%m-%dT%H:%M:%S.%f')

        obj = TestObject(self.fixture)
        # fields should be datetime objects
        self.assert_(isinstance(obj.date, datetime))
        self.assert_(isinstance(obj.dates[1], datetime))
        # inspect date parsing
        self.assertEqual(2010, obj.date.year)
        self.assertEqual(1, obj.date.month)
        self.assertEqual(3, obj.date.day)
        self.assertEqual(2, obj.date.hour)
        self.assertEqual(13, obj.date.minute)
        self.assertEqual(44, obj.date.second)
        # microsecond date parsing
        self.assertEqual(3000, obj.dates[1].microsecond)

        # set value via new datetime object
        today = datetime.today()
        obj.date = today
        self.assertEqual(obj.node.xpath('string(date)'), today.strftime('%Y-%m-%dT%H:%M:%S'))


    def testSchemaField(self):
        # very simple xsd schema and valid/invalid xml based on the one from lxml docs:
        #   http://codespeak.net/lxml/validation.html#xmlschema
        xsd = '''<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <xsd:element name="a" type="AType"/>
            <xsd:complexType name="AType">
                <xsd:sequence>
                    <xsd:element name="b" type="BType" />
                </xsd:sequence>
            </xsd:complexType>
            <xsd:simpleType name="BType">
                <xsd:restriction base="xsd:string">
                    <xsd:enumeration value="c"/>
                    <xsd:enumeration value="d"/>
                    <xsd:enumeration value="e"/>
                </xsd:restriction>
            </xsd:simpleType>
        </xsd:schema>
        '''
        FILE = tempfile.NamedTemporaryFile(mode="w")
        FILE.write(xsd)
        FILE.flush()

        valid_xml = '<a><b>some text</b></a>'

        class TestSchemaObject(xmlmap.XmlObject):
            XSD_SCHEMA = FILE.name
            txt = xmlmap.SchemaField('/a/b', 'BType', required=True)

        valid = xmlmap.load_xmlobject_from_string(valid_xml, TestSchemaObject)
        self.assertEqual('some text', valid.txt, 'schema field value is accessible as text')
        self.assert_(isinstance(valid._fields['txt'], xmlmap.StringField),
                'txt SchemaField with base string in schema initialized as StringField')
        self.assertEqual(['', 'c', 'd', 'e'], valid._fields['txt'].choices,
                'txt SchemaField has choices based on restriction enumeration in schema')

        # check required
        self.assertTrue(valid._fields['txt'].required)

        FILE.close()

    def testPredicatedSetting(self):
        class TestObject(xmlmap.XmlObject):
            attr_pred = xmlmap.StringField('pred[@a="foo"]')
            layered_pred = xmlmap.StringField('pred[@a="foo"]/pred[@b="bar"]')
            nested_pred = xmlmap.StringField('pred[pred[@a="foo"]]/val')

        obj = TestObject(self.fixture)

        obj.attr_pred = 'test'
        self.assertEqual(obj.node.xpath('string(pred[@a="foo"])'), 'test')

        obj.layered_pred = 'test'
        self.assertEqual(obj.node.xpath('string(pred[@a="foo"]/pred[@b="bar"])'), 'test')

        obj.nested_pred = 'test'
        self.assertEqual(obj.node.xpath('string(pred[pred[@a="foo"]]/val)'), 'test')


    def test_delete_constructed_xpath(self):
        # test deleting auto-constructed nodes
        class TestObject(xmlmap.XmlObject):
            multilevel_missing = xmlmap.StringField('missing_parent/missing_child')

        # deleting a nested xpath element should delete parent nodes
        obj = TestObject(self._empty_fixture())
        obj.multilevel_missing = 'text'
        del obj.multilevel_missing
        self.assertEqual(0, obj.node.xpath('count(missing_parent)'))

        class PredicateObject(xmlmap.XmlObject):
            text = xmlmap.StringField('missing[@type="foo"]/bar/text()')
            nested_attr = xmlmap.StringField('missing[@type="foo"]/bar[@type="foobar"]/@label')
            nested_text = xmlmap.StringField('missing[@type="foo"]/baz')
            child_pred = xmlmap.StringField('missing[@type="foo"][baz/@type="bah"]/txt')
            nested_pred = xmlmap.StringField('foo[@id="a"]/bar[@id="b"]/baz[@id="c"]/qux')

        obj = PredicateObject(self._empty_fixture())
        # set text and then delete
        obj.text = 'some text'
        del obj.text
        # parent path with predicate should be automatically removed
        self.assertEqual(0, obj.node.xpath('count(missing)'))

        # delete when another attribute is set
        # non-empty parent constructed path should NOT be removed
        obj = PredicateObject(self._empty_fixture())
        obj.nested_attr = 'tra'
        obj.text = 'la'
        del obj.text
        self.assertEqual(1, obj.node.xpath('count(missing/bar[@label])'))
        
        # separate text node under the constructed parent
        obj = PredicateObject(self._empty_fixture())
        obj.nested_attr = None
        obj.text = 'fa'
        obj.nested_text = 'la'
        del obj.text
        self.assertEqual(1, obj.node.xpath('count(missing/baz)'))

        # child predicates should work similarly to attributes
        obj = PredicateObject(self._empty_fixture())
        # set and then delete
        obj.child_pred = 'boo'
        del obj.child_pred
        # the entire path should be removed
        self.assertEqual(0, obj.node.xpath('count(missing)'))

        obj = PredicateObject(self._empty_fixture())
        # create them in this order so they will be in the same subtree
        obj.child_pred = 'boo'
        obj.text = 'la'
        del obj.text
        # text was removed
        self.assertEqual(0, obj.node.xpath('count(%s)' % obj._fields['text'].xpath))
        # parent element should NOT be removed because it is not empty
        self.assertEqual(1, obj.node.xpath('count(missing/baz[@type="bah"])'))

        # nested path steps with predicates should be removed
        obj = PredicateObject(self._empty_fixture())
        obj.nested_pred = 'la'
        del obj.nested_pred
        self.assertEqual(0, obj.node.xpath('count(foo)'))


# tests for settable listfields
class SubList(xmlmap.XmlObject):
    ROOT_NAME = 'sub'
    id = xmlmap.StringField('@id')
    parts = xmlmap.StringListField('part')

class ListTestObject(xmlmap.XmlObject):
    str = xmlmap.StringListField('baz')
    int = xmlmap.IntegerListField('bar')
    letters = xmlmap.StringListField('l')
    empty = xmlmap.StringListField('missing')
    nodes = xmlmap.NodeListField('sub', SubList)

class TestNodeList(unittest.TestCase):
    FIXTURE_TEXT = '''
        <foo>
            <baz>forty-two</baz>
            <baz>thirteen</baz>
            <bar>42</bar>
            <bar>13</bar>
            <l>a</l>
            <l>b</l>
            <l>a</l>
            <l>3</l>
            <l>c</l>
            <l>a</l>
            <l>7</l>
            <l>b</l>
            <l>11</l>
            <l>a</l>
            <l>y</l>
            <sub id="007">
               <part>side-a</part>
               <part>side-b</part>
            </sub>
        </foo>
    '''
    
    def setUp(self):

        # parseString wants a url. let's give it a proper one.
        url = '%s#%s.%s' % (__file__, self.__class__.__name__, 'FIXTURE_TEXT')

        self.fixture = xmlmap.parseString(self.FIXTURE_TEXT, url)
        self.obj = ListTestObject(self.fixture)

    def test_index_checking(self):
        self.assertRaises(TypeError, self.obj.str.__getitem__, 'a')
        self.assertRaises(AssertionError, self.obj.str.__getitem__, slice(0, 10))
        self.assertRaises(TypeError, self.obj.str.__setitem__, 'a', 'val')
        self.assertRaises(AssertionError, self.obj.str.__setitem__, slice(0, 10), ['val'])
        self.assertRaises(TypeError, self.obj.str.__delitem__, 'a')
        self.assertRaises(AssertionError, self.obj.str.__delitem__, slice(0, 10))

    def test_equals(self):
        # custom equal/not equals allows comparing to normal lists
        self.assertTrue(self.obj.int == [42, 13])
        self.assertFalse(self.obj.int != [42, 13])
        self.assertFalse(self.obj.int == [42, 5])
        self.assertTrue(self.obj.int != [45, 13])

        self.assertTrue(self.obj.str == ['forty-two', 'thirteen'])
        self.assertFalse(self.obj.str != ['forty-two', 'thirteen'])
        self.assertFalse(self.obj.str == ['nine', 'thirteen'])
        self.assertTrue(self.obj.str != ['nine', 'sixteen'])

    def test_set(self):           
        # set string values
        string_list = self.obj.str
        # - existing nodes in the xml
        new_val = 'twenty-four'
        self.obj.str[0] = new_val
        self.assertEqual(new_val, self.obj.str[0],
            'set value of existing node (position 0) in StringListField - expected %s, got %s' % \
            (new_val, self.obj.str[0]))
        new_val = 'seven'
        string_list[1] = new_val
        self.assertEqual(new_val, string_list[1],
            'set value of existing node (position 1) in StringListField - expected %s, got %s' % \
            (new_val, string_list[1]))
        # - new value for a node at the end of the list - node should be created
        new_val = 'eleventy-one'
        string_list[2] = new_val
        self.assertEqual(new_val, string_list[2],
            'set value of new node (position 2) in StringListField - expected %s, got %s' % \
            (new_val, string_list[2]))
        # - beyond end of current list
        self.assertRaises(IndexError, string_list.__setitem__, 4, 'foo')

        # integer values
        int_list = self.obj.int
        # - existing nodes in the xml
        new_val = 24
        int_list[0] = new_val
        self.assertEqual(new_val, int_list[0],
            'set value of existing node (position 0) in IntegerListField - expected %d, got %d' % \
            (new_val, int_list[0]))
        new_val = 7
        int_list[1] = new_val
        self.assertEqual(new_val, int_list[1],
            'set value of existing node (position 1) in IntegerListField - expected %d, got %d' % \
            (new_val, int_list[1]))
        # - a new value for a node at the end of the list - node should be created
        new_val = 111
        int_list[2] = new_val
        self.assertEqual(new_val, int_list[2],
            'set value of new node (position 2) in IntegerListField - expected %d, got %d' % \
            (new_val, int_list[2]))
        # - beyond end of current list
        self.assertRaises(IndexError, int_list.__setitem__, 4, 23)

        # list with no current members
        self.obj.empty[0] = 'foo'
        self.assertEqual(1, len(self.obj.empty),
            "length of empty list after setting at index 0 should be 1, got %d" % \
            len(self.obj.empty))
        self.assertEqual('foo', self.obj.empty[0])

        # set a nodefield
        # append node - create sublist object and append
        newnode = SubList()
        newnode.id = '1a'
        newnode.parts.extend(['leg', 'foot'])
        self.obj.nodes[0] = newnode
        self.assertEqual(newnode.id, self.obj.nodes[0].id,
            "subfield id attribute matches new node after set")
        self.assertEqual(['leg', 'foot'], self.obj.nodes[0].parts,
            "subfield parts attribute matches new node after set")

        # test setting entire list at once
        # - string list
        xyz = ['x', 'y', 'z']
        self.obj.letters = xyz		# shorter than current list
        self.assertEqual(xyz, self.obj.letters)
        abc = ['a', 'b', 'c']
        self.obj.letters = abc		# equal length to current list
        self.assertEqual(abc, self.obj.letters)

        abcdef = ['a', 'b', 'c', 'd', 'e', 'f']
        self.obj.letters = abcdef	# longer than current list
        self.assertEqual(abcdef, self.obj.letters)
        # set to empty list
        self.obj.letters = []
        self.assertEqual([], self.obj.letters)

        # - integer list
        nums = [33, 42, 77]
        self.obj.int = nums
        self.assertEqual(nums, self.obj.int)

        # - empty list
        new_empties = ['gone', 'lost']
        self.obj.empty = new_empties
        self.assertEqual(new_empties, self.obj.empty)

        # - node list
        new_nodelist = [SubList(id='01', parts=['a', 'b']),
                          SubList(id='02', parts=['c', 'd']),
                          SubList(id='03', parts=['m', 'n'])]
        self.obj.nodes = new_nodelist
        self.assertEqual(new_nodelist, self.obj.nodes)


    def test_del(self):
        # first element
        del(self.obj.str[0])
        self.assertEqual(1, len(self.obj.str),
            "StringListField length should be 1 after deletion, got %d" % len(self.obj.str))
        self.assertEqual('thirteen', self.obj.str[0])

        # second/last element
        int_list = self.obj.int
        del(int_list[1])
        self.assertEqual(1, len(int_list),
            "IntegerListField length should be 1 after deletion, got %d" % len(int_list))

        # out of range
        self.assertRaises(IndexError, int_list.__delitem__, 4)
        self.assertRaises(IndexError, self.obj.empty.__delitem__, 0)

        # delete a nodelistfield item
        del(self.obj.nodes[0])
        self.assertEqual(0, len(self.obj.nodes),
            "NodeListField length should be 0 after deletion, got %d" % len(self.obj.nodes))

    def test_count(self):
        self.assertEqual(4, self.obj.letters.count('a'))
        self.assertEqual(2, self.obj.letters.count('b'))
        self.assertEqual(0, self.obj.letters.count('z'))
        
        self.assertEqual(0, self.obj.empty.count('z'))

        # nodelistfield
        node = SubList()
        node.id = '1a'
        node.parts.extend(['ankle', 'toe'])
        # before adding
        self.assertEqual(0, self.obj.nodes.count(node))
        self.obj.nodes.append(node)
        # after adding (same node can't be added more than once)
        self.assertEqual(1, self.obj.nodes.count(node))

    def test_append(self):
        self.obj.str.append('la')
        self.assertEqual(3, len(self.obj.str),
            "length of StringListField is 3 after appending value")
        self.assertEqual('la', self.obj.str[2])

        int_list = self.obj.int
        int_list.append(9)
        self.assertEqual(3, len(int_list),
            "length of IntegerListField is 3 after appending value")
        self.assertEqual(9, int_list[2])

        # list with no current members
        self.obj.empty.append('foo')
        self.assertEqual(1, len(self.obj.empty),
            "length of empty list after setting appending should be 1, got %d" % \
            len(self.obj.empty))
        self.assertEqual('foo', self.obj.empty[0])

        # append node - create sublist object and append
        newnode = SubList()
        newnode.id = '1a'
        newnode.parts.append('leg')
        newnode.parts.append('foot')
        self.obj.nodes.append(newnode)
        self.assertEqual(2, len(self.obj.nodes),
            "length of NodeListField should be 2 after appending node, got %d" \
                % len(self.obj.nodes))
        self.assertEqual('1a', self.obj.nodes[1].id)
        self.assertEqual('leg', self.obj.nodes[1].parts[0])
        self.assertEqual('foot', self.obj.nodes[1].parts[1])
        # append another
        node2 = SubList()
        node2.id = '2b'
        self.obj.nodes.append(node2)
        self.assertEqual(3, len(self.obj.nodes),
            "length of NodeListField should be 3 after appending second node, got %d" \
                % len(self.obj.nodes))
        self.assertEqual(node2.id, self.obj.nodes[2].id)


    def test_index(self):
        letters = self.obj.letters
        self.assertEqual(0, letters.index('a'))
        self.assertEqual(1, letters.index('b'))
        self.assertEqual(3, letters.index('3'))

        # not in list
        self.assertRaises(ValueError, letters.index, 'foo')
        self.assertRaises(ValueError, self.obj.empty.index, 'foo')

        # nodelistfield
        node = SubList()
        node.id = '1a'
        node.parts.extend(['ankle', 'toe'])
        self.obj.nodes.insert(0, node)
        self.assertEqual(0, self.obj.nodes.index(node),
            "index returns 0 for nodefield inserted at position 0")
        # delete and append to the end
        del(self.obj.nodes[0])
        self.obj.nodes.append(node)
        self.assertEqual(1, self.obj.nodes.index(node),
            "index returns 1 for nodefield appended to nodefield list of with 1 item")    

    def test_remove(self):
        letters = self.obj.letters
        letters.remove('a')
        self.assertNotEqual('a', letters[0],
            "first letter is no longer 'a' after removing 'a'")
        self.assertEqual(1, letters.index('a'),
            "index for 'a' is 1 after removing 'a' - expected 1, got %d" % letters.index('a'))

        # not in list
        self.assertRaises(ValueError, letters.remove, 'foo')
        self.assertRaises(ValueError, self.obj.empty.remove, 'foo')

        # nodelistfield
        node = SubList()
        node.id = '1a'
        node.parts.extend(['ankle', 'toe'])
        # node is not in the list
        self.assertRaises(ValueError, self.obj.nodes.remove, node)
        # append then remove
        self.obj.nodes.append(node)
        self.obj.nodes.remove(node)
        self.assert_(node not in self.obj.nodes, "node is not in NodeList after remove")

    def test_pop(self):
        last = self.obj.letters.pop()
        self.assertEqual('y', last,
            "pop with no index returned last letter in list - expected 'y', got '%s'" % last)
        self.assert_('y' not in self.obj.letters,
            "'y' not in stringlistfield after popping last element")

        first = self.obj.letters.pop(0)
        self.assertEqual('a', first,
            "pop with index 0 returned first letter in list - expected 'a', got '%s'" % first)
        self.assertNotEqual('a', self.obj.letters[0],
            "first letter is no longer 'a' after pop index 0")

        # out of range
        self.assertRaises(IndexError, self.obj.empty.pop, 0)
        self.assertRaises(IndexError, self.obj.empty.pop)

        # node
        node = self.obj.nodes.pop()
        self.assert_(isinstance(node, SubList), "popped node is ")
        self.assertEqual('007', node.id, "popped node has expected id")
        self.assertEqual(['side-a', 'side-b'], node.parts, "popped node has expected parts")

    def test_extend(self):
        letters = self.obj.letters
        letters.extend(['w', 'd', '40'])
        self.assert_('w' in letters, 'value in extend list is now in StringList')
        self.assert_('d' in letters, 'value in extend list is now in StringList')
        self.assertEqual('40', letters[len(letters) - 1],
            'last value in extend list is now last element StringList')

        # extend an empty list
        new_list = ['a', 'b', 'c']
        self.obj.empty.extend(new_list)
        self.assertEqual(new_list, self.obj.empty)

        # extend node list
        node1 = SubList()
        node1.id = '1a'
        node1.parts.extend(['hand', 'finger'])
        node2 = SubList()
        node2.id = '2b'
        self.obj.nodes.extend([node1, node2])
        self.assertEqual(3, len(self.obj.nodes),
            "length of nodelistfield should be 3 after extending with 2 nodes, got %d" \
            % len(self.obj.nodes))
        self.assertEqual(node1.id, self.obj.nodes[1].id)
        self.assertEqual(node2.id, self.obj.nodes[2].id)        

    def test_insert(self):
        letters = self.obj.letters
        orig_letters = list(letters.data)   # copy original letters for comparison
        # insert somewhere in the middle
        letters.insert(2, 'q')
        self.assertEqual('q', letters[2],
            "letters[2] should be 'q' after inserting 'q' at 2, got '%s'" % letters[2])
        self.assertEqual(len(orig_letters)+1, len(letters),
            "length of letters should increase by 1 after insert; expected %d, got length %d" \
                % (len(orig_letters)+1, len(letters) ))
        self.assertEqual(orig_letters[2], letters[3],
            "original 3rd letter should be 4th letter after insert; expected '%s', got '%s'" % \
                (orig_letters[2], letters[3]))

        # insert at beginning
        letters.insert(0, 'z')
        self.assertEqual('z', letters[0],
            "letters[0] should be 'z' after inserting 'z' at 0, got '%s'" % letters[0])
        self.assertEqual(len(orig_letters)+2, len(letters),
            "length of letters should increase by 2 after 2nd insert; expected %d, got length %d" \
                % (len(orig_letters)+2, len(letters) ))
        self.assertEqual(orig_letters[0], letters[1],
            "original first letter should be 2nd letter after insert; expected '%s', got '%s'" % \
                (orig_letters[0], letters[1]))

        # 'insert' at the end
        letters.insert(len(letters), '99')
        self.assertEqual('99', letters[-1],
            "last item in letters should be '99' after inserting at end; got '%s'" % letters[-1])

        # out of range
        self.assertRaises(IndexError, letters.insert, 99, 'bar')

        # insert in empty list
        self.obj.empty.insert(0, 'z')
        self.assertEqual('z', self.obj.empty[0],
            "empty[0] should be 'z' after inserting 'z' at 0, got '%s'" % self.obj.empty[0])
        self.assertEqual(1, len(self.obj.empty))

        # insert node
        node = SubList()
        node.id = '1a'
        node.parts.extend(['hand', 'finger'])
        self.obj.nodes.insert(0, node)
        self.assertEqual(2, len(self.obj.nodes),
            "length of nodelistfield should be 2 after inserting node, got %d" \
            % len(self.obj.nodes))
        self.assertEqual(node.id, self.obj.nodes[0].id)
        self.assertEqual(node.parts, self.obj.nodes[0].parts)


if __name__ == '__main__':
    main()
