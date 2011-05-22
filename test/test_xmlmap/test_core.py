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

from lxml import etree
from os import path
import unittest
import tempfile

import eulxml.xmlmap.core as xmlmap
from testcore import main

class TestXsl(unittest.TestCase):
    FIXTURE_TEXT = '''
        <foo>
            <bar>
                <baz>42</baz>
            </bar>
            <bar>
                <baz>13</baz>
            </bar>
        </foo>
    '''
    # simple xsl for testing xslTransform - converts bar/baz to just baz
    FIXTURE_XSL = '''<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
        <xsl:template match="bar">
            <xsl:apply-templates select="baz"/>
            </xsl:template>

        <xsl:template match="@*|node()">
            <xsl:copy>
                <xsl:apply-templates select="@*|node()"/>
            </xsl:copy>
        </xsl:template>

    </xsl:stylesheet>'''

    INVALID_XSL = '''
    <xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
        <xsl:template match="/">
            <none>
            <xsl:value-of select="$foo"/>
            </none>
        </xsl:template>
    </xsl:stylesheet>
    '''
    
    def setUp(self):
        # parseString wants a url. let's give it a proper one.
        url = '%s#%s.%s' % (__file__, self.__class__.__name__, 'FIXTURE_TEXT')
        self.fixture = xmlmap.parseString(self.FIXTURE_TEXT, url)

    def test_xsl_transform(self):
        class TestObject(xmlmap.XmlObject):
            bar_baz = xmlmap.StringField('bar[1]/baz')
            nobar_baz = xmlmap.StringField('baz[1]')

        # xsl in string
        obj = TestObject(self.fixture)
        newobj = obj.xsl_transform(xsl=self.FIXTURE_XSL, return_type=TestObject)
        self.assertEqual('42', newobj.nobar_baz)
        self.assertEqual(None, newobj.bar_baz)

        # xsl in file
        self.FILE = tempfile.NamedTemporaryFile(mode="w")
        self.FILE.write(self.FIXTURE_XSL)
        self.FILE.flush()

        obj = TestObject(self.fixture)
        newobj = obj.xsl_transform(filename=self.FILE.name, return_type=TestObject)
        self.assertEqual('42', newobj.nobar_baz)
        self.assertEqual(None, newobj.bar_baz)

        self.FILE.close()
        # not yet tested: xsl with parameters


# NOTE: using TestXsl fixture text for the init tests

class TestXmlObjectStringInit(unittest.TestCase):
    # example invalid document from 4suite documentation
    INVALID_XML = """<!DOCTYPE a [
  <!ELEMENT a (b, b)>
  <!ELEMENT b EMPTY>
]>
<a><b/><b/><b/></a>"""
    VALID_XML = """<!DOCTYPE a [
  <!ELEMENT a (b, b)>
  <!ELEMENT b EMPTY>
]>
<a><b/><b/></a>"""
    def test_load_from_string(self):
        """Test using shortcut to initialize XmlObject from string"""
        obj = xmlmap.load_xmlobject_from_string(TestXsl.FIXTURE_TEXT)
        self.assert_(isinstance(obj, xmlmap.XmlObject))

    def test_load_from_string_with_classname(self):
        """Test using shortcut to initialize named XmlObject class from string"""
        
        class TestObject(xmlmap.XmlObject):
            pass
        
        obj = xmlmap.load_xmlobject_from_string(TestXsl.FIXTURE_TEXT, TestObject)
        self.assert_(isinstance(obj, TestObject))

    def test_load_from_string_with_validation(self):
       
        self.assertRaises(Exception, xmlmap.load_xmlobject_from_string, self.INVALID_XML, validate=True)
        # fixture with no doctype also causes a validation error
        self.assertRaises(Exception, xmlmap.load_xmlobject_from_string,
            TestXsl.FIXTURE_TEXT, validate=True)

        obj = xmlmap.load_xmlobject_from_string(self.VALID_XML)
        self.assert_(isinstance(obj, xmlmap.XmlObject))

        
class TestXmlObjectFileInit(unittest.TestCase):
    
    def setUp(self):
        self.FILE = tempfile.NamedTemporaryFile(mode="w")
        self.FILE.write(TestXsl.FIXTURE_TEXT)
        self.FILE.flush()

        # valid and invalid examples with a simple doctype
        self.VALID = tempfile.NamedTemporaryFile(mode="w")
        self.VALID.write(TestXmlObjectStringInit.VALID_XML)
        self.VALID.flush()

        self.INVALID = tempfile.NamedTemporaryFile(mode="w")
        self.INVALID.write(TestXmlObjectStringInit.INVALID_XML)
        self.INVALID.flush()

    def tearDown(self):
        self.FILE.close()
    def test_load_from_file(self):
        """Test using shortcut to initialize XmlObject from a file"""
        obj = xmlmap.load_xmlobject_from_file(self.FILE.name)
        self.assert_(isinstance(obj, xmlmap.XmlObject))

    def test_load_from_file_with_classname(self):
        """Test using shortcut to initialize named XmlObject class from string"""
        
        class TestObject(xmlmap.XmlObject):
            pass
        
        obj = xmlmap.load_xmlobject_from_file(self.FILE.name, TestObject)
        self.assert_(isinstance(obj, TestObject))

    def test_load_from_file_with_validation(self):
        # has doctype, but not valid
        self.assertRaises(Exception, xmlmap.load_xmlobject_from_file, self.INVALID.name, validate=True)
        # no doctype
        self.assertRaises(Exception, xmlmap.load_xmlobject_from_file, self.FILE.name, validate=True)
        # doctype, valid
        obj = xmlmap.load_xmlobject_from_file(self.VALID.name, validate=True)
        self.assert_(isinstance(obj, xmlmap.XmlObject))

class TestXmlObject(unittest.TestCase):

    def setUp(self):
        self.obj = xmlmap.load_xmlobject_from_string(TestXsl.FIXTURE_TEXT)
        
    def test__unicode(self):
        u = self.obj.__unicode__()
        self.assert_("42 13" in u)

    def test__string(self):
        self.assertEqual('42 13', self.obj.__string__())

        # convert xml with unicode content
        obj = xmlmap.load_xmlobject_from_string(u'<text>unicode \u2026</text>')
        self.assertEqual('unicode &#8230;', obj.__string__())

    def test_serialize_tostring(self):
        xml_s = self.obj.serialize()        
        self.assert_("<baz>42</baz>" in xml_s)

        # serialize subobjects
        baz = self.obj.node.xpath('bar/baz[1]')[0]
        baz_obj = xmlmap.XmlObject(baz)
        self.assertEqual('<baz>42</baz>', baz_obj.serialize().strip())

    def test_serialize_tofile(self):
        FILE = tempfile.TemporaryFile()
        self.obj.serialize(stream=FILE)
        FILE.flush()
        FILE.seek(0)
        self.assert_("<baz>13</baz>" in FILE.read())
        FILE.close()

    def test_serializeDocument(self):
        obj = xmlmap.load_xmlobject_from_string(TestXmlObjectStringInit.VALID_XML)
        xmlstr = obj.serializeDocument()
        self.assert_("encoding='UTF-8'" in xmlstr,
            "XML generated by serializeDocument should include xml character encoding")
        self.assert_('<!DOCTYPE a' in xmlstr,
            "XML generated by serializeDocument should include DOCTYPE declaration")

    def test_isvalid(self):
        # attempting schema-validation on an xmlobject with no schema should raise an exception
        self.assertRaises(Exception, self.obj.schema_valid)

        # generic validation with no schema -- assumed True
        self.assertTrue(self.obj.is_valid())

        # very simple xsd schema and valid/invalid xml taken from lxml docs:
        #   http://codespeak.net/lxml/validation.html#xmlschema
        xsd = '''<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <xsd:element name="a" type="AType"/>
            <xsd:complexType name="AType">
                <xsd:sequence>
                    <xsd:element name="b" type="xsd:string" />
                </xsd:sequence>
            </xsd:complexType>
        </xsd:schema>
        '''
        FILE = tempfile.NamedTemporaryFile(mode="w")
        FILE.write(xsd)
        FILE.flush()

        valid_xml = '<a><b></b></a>'
        invalid_xml = '<a foo="1"><c></c></a>'

        class TestSchemaObject(xmlmap.XmlObject):
            XSD_SCHEMA = FILE.name
        
        valid = xmlmap.load_xmlobject_from_string(valid_xml, TestSchemaObject)
        self.assertTrue(valid.is_valid())
        self.assertTrue(valid.schema_valid())

        invalid = xmlmap.load_xmlobject_from_string(invalid_xml, TestSchemaObject)        
        self.assertFalse(invalid.is_valid())
        invalid.is_valid()
        self.assertEqual(2, len(invalid.validation_errors()))

        # do schema validation at load time
        valid = xmlmap.load_xmlobject_from_string(valid_xml, TestSchemaObject,
            validate=True)
        self.assert_(isinstance(valid, TestSchemaObject))

        self.assertRaises(etree.XMLSyntaxError, xmlmap.load_xmlobject_from_string,
            invalid_xml, TestSchemaObject, validate=True)

        FILE.close()

    def test_equal(self):
        class SubObj(xmlmap.XmlObject):
            baz = xmlmap.StringField('baz')
        class XmlObj(xmlmap.XmlObject):
            bar = xmlmap.NodeField('bar', SubObj)
            bar_list = xmlmap.NodeListField('bar', SubObj)
            generic = xmlmap.NodeField('bar', xmlmap.XmlObject)

        obj = xmlmap.load_xmlobject_from_string(TestXsl.FIXTURE_TEXT, XmlObj)
        self.assertTrue(obj == obj,
            'xmlobject identity equals obj == obj should return True')
        self.assertFalse(obj.bar != obj.bar,
            'xmlobject identity not-equals obj != obj should return False')
        self.assertTrue(obj.bar == obj.bar_list[0],
            'xmlobject equal should return True for objects pointing at same document node')
        self.assertFalse(obj.bar != obj.bar_list[0],
            'xmlobject not equal should return False for objects pointing at same document node')
        self.assertTrue(obj.bar != obj.bar_list[1],
            'xmlobject not equal should return True for objects pointing at different nodes')
        self.assertFalse(obj.bar == obj.bar_list[1],
            'xmlobject equal should return False for object pointing at different nodes')
        obj2 = xmlmap.load_xmlobject_from_string(TestXsl.FIXTURE_TEXT, XmlObj)
        self.assertTrue(obj == obj2,
            'two different xmlobjects that serialize the same should be considered equal')

        # compare to None
        self.assertTrue(obj != None,
            'xmlobject not equal to None should return True')
        self.assertFalse(obj.bar == None,
            'xmlobject equal None should return False')

        # FIXME: is this really what we want?
        # should different xmlobject classes pointing at the same node be considered equal?
        self.assertTrue(obj.generic == obj.bar,
            'different xmlobject classes pointing at the same node are considered equal')

    def test_quickinit(self):
        class XmlObj(xmlmap.XmlObject):
            ROOT_NAME = 'foo'
            id = xmlmap.StringField('@id')
            strings = xmlmap.StringListField('str')
            int = xmlmap.IntegerField('int')
            bool = xmlmap.SimpleBooleanField('bool', 'yes', 'no')

        init_values = {
            'id': '2b',
            # NOTE: setting a listfield like this is currently not supported (but would be cool)
            #'strings': ['one', 'two', 'three'],
            'int': 5,
            'bool': True
            }
        obj = XmlObj(**init_values)
        self.assertEqual(init_values['id'], obj.id)
        self.assertEqual(init_values['int'], obj.int)
        self.assertEqual(init_values['bool'], obj.bool)

class TestLoadSchema(unittest.TestCase):
    
    def test_load_schema(self):
        schema = xmlmap.loadSchema('http://www.w3.org/2001/xml.xsd')
        self.assert_(isinstance(schema, etree.XMLSchema),
            'loadSchema should return an etree.XMLSchema object when successful')

    def test_load_after_parsestring(self):
        # lxml 2.2.7 (used internally by xmlmap) has a bug that causes
        # lxml.etree.parse() to fail after a call to
        # lxml.etree.fromstring(). this causes the second call below to fail
        # unless we work around that bug in xmlmap.
        xmlmap.parseString('<foo/>') # has global side effects in lxml
        xmlmap.loadSchema('http://www.w3.org/2001/xml.xsd') # fails
    
    def test_ioerror(self):
        # IO error - file path is wrong/incorrect OR network-based schema unavailable
        self.assertRaises(IOError, xmlmap.loadSchema, '/bogus.xsd')
        try:
            xmlmap.loadSchema('/bogus.xsd')
        except IOError as io_err:
            self.assert_('bogus.xsd' in str(io_err),
                'exception message indicates load error on specific document')
        self.assertRaises(IOError, xmlmap.loadSchema, '/bogus.xsd', 'file://some/dir')

    def test_parse_error(self):
        # test document that is loaded but can't be parsed as a schema
        # valid xml non-schema doc
        xmldoc = path.join(path.dirname(path.abspath(__file__)), 'fixtures', 'heaney653.xml')
        # confirm an exception is raised
        self.assertRaises(etree.XMLSchemaParseError, xmlmap.loadSchema, xmldoc)
        # inspect the exception for expected detail in error messages
        try:
            xmlmap.loadSchema(xmldoc)
        except etree.XMLSchemaParseError as parse_err:
            self.assert_('Failed to parse schema %s' % xmldoc in str(parse_err),
                'schema parse exception includes detail about schema document that failed')
            self.assert_('not a schema document' in str(parse_err),
                'schema parse exception includes detail about why parsing failed')

        # schema that attempts to import something inaccessible
        xsd = '''<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <xsd:import namespace="http://www.w3.org/1999/xlink"
                schemaLocation="file://cant/catch/me/xlink.xsd"/>
            <xsd:element name="a" type="xlink:simpleLink"/>
        </xsd:schema>
        '''
        FILE = tempfile.NamedTemporaryFile(mode="w")
        FILE.write(xsd)
        FILE.flush()
        # assert this causes the expected exception
        self.assertRaises(etree.XMLSchemaParseError, xmlmap.loadSchema,
                          FILE.name)
        # use try/except to inspect the error message
        try:
            xmlmap.loadSchema(FILE.name)
        except etree.XMLSchemaParseError as parse_err:
            self.assert_('Failed to parse' in str(parse_err),
                'schema parse exception includes detail about what went wrong')

if __name__ == '__main__':
    main()
