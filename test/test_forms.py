# file test_forms.py
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

import re
import unittest
from mock import patch

# must be set before importing anything from django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'testsettings'

from django import forms
from django.conf import settings
from django.forms import ValidationError
from django.forms.formsets import BaseFormSet

from eulxml import xmlmap
from eulxml.xmlmap.fields import DateTimeField     # not yet supported - testing for errors
from eulxml.forms import XmlObjectForm, xmlobjectform_factory, SubformField
from eulxml.forms.xmlobject import XmlObjectFormType, BaseXmlObjectListFieldFormSet, \
     ListFieldForm, IntegerListFieldForm

from testcore import main

# test xmlobject and xml content to generate test form

class TestSubobject(xmlmap.XmlObject):
    ROOT_NAME = 'bar'
    val = xmlmap.IntegerField('baz', required=False)
    id2 = xmlmap.StringField('@id')

class OtherTestSubobject(TestSubobject):
    ROOT_NAME = 'plugh'

class TestObject(xmlmap.XmlObject):
    ROOT_NAME = 'foo'
    id = xmlmap.StringField('@id', verbose_name='My Id', help_text='enter an id')
    int = xmlmap.IntegerField('bar[2]/baz')
    bool = xmlmap.SimpleBooleanField('boolean', 'yes', 'no')
    longtext = xmlmap.StringField('longtext', normalize=True, required=False)
    child = xmlmap.NodeField('bar[1]', TestSubobject, verbose_name='Child bar1')
    children = xmlmap.NodeListField('bar', TestSubobject)
    other_child = xmlmap.NodeField('plugh', OtherTestSubobject)
    my_opt = xmlmap.StringField('opt', choices=['a', 'b', 'c'])
    text = xmlmap.StringListField('text')
    numbers = xmlmap.IntegerListField('number')

FIXTURE_TEXT = '''
    <foo id='a'>
        <bar id='forty-two'>
            <baz>42</baz>
        </bar>
        <bar>
            <baz>13</baz>
        </bar>
        <boolean>yes</boolean>
        <longtext>here is a bunch of text too long for a text input</longtext>
        <text>la</text><text>fa</text>
    </foo>
'''
class TestForm(XmlObjectForm):
    class Meta:
        model = TestObject


class XmlObjectFormTest(unittest.TestCase):

    # sample POST data for testing form update logic (used by multiple tests)
    post_data = {
        'child-id2': 'two',
        'child-val': 2,
        # include base form data so form will be valid
        'longtext': 'completely new text content',
        'int': 21,
        'bool': False,
        'id': 'b',
        'my_opt': 'c',
        'other_child-val': '0',
        'other_child-id2': 'xyzzy',
        # children formset
        'children-TOTAL_FORMS': 5,
        'children-INITIAL_FORMS': 2,
        'children-0-id2': 'two',
        'children-0-val': 2,
        'children-1-id2': 'twenty-one',
        'children-1-val': 21,
        'children-2-id2': 'five',
        'children-2-val': 5,
        'children-3-id2': 'four',
        'children-3-val': 20,
        # stringlist formset
        'text-TOTAL_FORMS': 1,
        'text-INITIAL_FORMS': 0,
        'text-0-val': 'foo',
        # integerlist formset
        'numbers-TOTAL_FORMS': 0,
        'numbers-INITIAL_FORMS': 0,
        }

    def setUp(self):
        # instance of form with no test object
        self.new_form = TestForm()
        # instance of form with test object instance
        self.testobj = xmlmap.load_xmlobject_from_string(FIXTURE_TEXT, TestObject)
        self.update_form = TestForm(instance=self.testobj)

    def tearDown(self):
        pass

    def test_simple_fields(self):
        # there should be a form field for each simple top-level xmlmap field
        
        # note: currently formobject uses field name for formfield label, but that could change
        formfields = self.new_form.base_fields

        self.assert_('int' in formfields, 'int field is present in form fields')
        self.assert_(isinstance(formfields['int'], forms.IntegerField),
            "xmlmap.IntegerField 'int' initialized as IntegerField")
        expected, got = 'Int', formfields['int'].label
        self.assertEqual(expected, got, "form field label should be set to " + \
            "xmlmap field name; expected %s, got %s" % (expected, got))

        self.assert_('id' in formfields, 'id field is present in form fields')
        self.assert_(isinstance(formfields['id'], forms.CharField),
            "xmlmap.StringField 'id' field initialized as CharField")
        expected, got = 'My Id', formfields['id'].label
        self.assertEqual(expected, got, "form field label should be set to " + \
            "from xmlmap field verbose name; expected %s, got %s" % (expected, got))
        expected, got = 'enter an id', formfields['id'].help_text
        self.assertEqual(expected, got, "form field help text should be set to " + \
            "from xmlmap field help text; expected %s, got %s" % (expected, got))

        self.assert_('bool' in formfields, 'bool field is present in form fields')
        self.assert_(isinstance(formfields['bool'], forms.BooleanField),
            "xmlmap.SimpleBooleanField 'bool' field initialized as BooleanField")
        expected, got = 'Bool', formfields['bool'].label
        self.assertEqual(expected, got, "form field label should be set to " + \
            "xmlmap field name; expected %s, got %s" % (expected, got))

        # choice field
        self.assert_('my_opt' in formfields, 'my_opt field is present in form fields')
        self.assert_(isinstance(formfields['my_opt'], forms.ChoiceField),
            "xmlmap.StringField 'my_opt' with choices form field initialized as ChoiceField")
        expected, got = 'My Opt', formfields['my_opt'].label
        self.assertEqual(expected, got, "form field label should be set to " + \
            "xmlmap field name; expected %s, got %s" % (expected, got))

        # required value from xmlobject field
        self.assertFalse(formfields['longtext'].required,
            'form field generated from xmlobject field with required=False is not required')

    def test_unchanged_initial_param(self):
        # initial data dictionary passed in should not be changed by class init
        my_initial_data = {'foo': 'bar'}
        initial_copy = my_initial_data.copy()
        TestForm(instance=self.testobj, initial=initial_copy)
        self.assertEqual(my_initial_data, initial_copy)

    def test_field_value_from_instance(self):
        # when form is initialized from an xmlobject instance, form should 
        # have initial field values be pulled from the xml object
        
        initial_data = self.update_form.initial   # initial values set on BaseForm
        expected, got = 'a', initial_data['id']
        self.assertEqual(expected, got,
            "initial instance-based form value for 'id' should be %s, got %s" % \
            (expected, got))

        expected, got = 13, initial_data['int']
        self.assertEqual(expected, got,
           "initial instance-based form value for 'int' should be %s, got %s" % \
            (expected, got))

        expected, got = True, initial_data['bool']
        self.assertEqual(expected, got,
           "initial instance-based form value for 'bool' should be %s, got %s" % \
            (expected, got))

        # test with prefixes
        update_form = TestForm(instance=self.testobj, prefix='pre')
        initial_data = update_form.initial   # initial values set on BaseForm
        expected, got = 'a', initial_data['id']
        self.assertEqual(expected, got,
            "initial instance-based form value for 'pre-id' should be %s, got %s" % \
            (expected, got))
        # the *rendered* field should actually have the value
        # ... there should probably be a way to inspect the BoundField value directly (can't get it to work)
        self.assert_('value="%s"' % expected in str(update_form['id']),
            'rendered form field has correct initial value')
        self.assert_('name="pre-id"' in str(update_form['id']),
            'rendered form field has a name with the requested prefix')
        self.assert_('id="id_pre-id"' in str(update_form['id']),
            'rendered form field has an id with the requested prefix')

        expected, got = 13, initial_data['int']
        self.assertEqual(expected, got,
           "initial instance-based form value for 'int' should be %s, got %s" % \
            (expected, got))

        expected, got = True, initial_data['bool']
        self.assertEqual(expected, got,
           "initial instance-based form value for 'bool' should be %s, got %s" % \
            (expected, got))

    def test_xmlobjectform_factory(self):
        form = xmlobjectform_factory(TestObject)
        # creates and returns a new form class of type XmlObjectFormType
        self.assert_(isinstance(form, XmlObjectFormType),
            'factory-generated form class is of type XmlObjectFormType')

        expected, got = 'TestObjectXmlObjectForm', form.__name__
        self.assertEqual(expected, got,
            "factory-generated form class has a reasonable name; expected %s, got %s" % \
            (expected, got))
        self.assertEqual(TestObject, form.Meta.model,
            "xmlobject class 'TestObject' correctly set as model in form class Meta")

        # specify particular fields - should be set in form Meta
        form = xmlobjectform_factory(TestObject, fields=['int', 'bool'])        
        self.assert_('int' in form.Meta.fields)
        self.assert_('bool' in form.Meta.fields)
        self.assert_('id' not in form.Meta.fields)

        # exclude particular fields - should be set in form Meta
        form = xmlobjectform_factory(TestObject, exclude=['int', 'bool'])
        self.assert_('int' in form.Meta.exclude)
        self.assert_('bool' in form.Meta.exclude)
        self.assert_('id' not in form.Meta.exclude)

    def test_specified_fields(self):
        # if fields are specified, only they should be listed
        myfields = ['int', 'bool', 'child.val']
        myform = xmlobjectform_factory(TestObject, fields=myfields)
        form = myform()
        self.assert_('int' in form.base_fields,
            'int field is present in form fields when specified in field list')
        self.assert_('bool' in form.base_fields,
            'bool field is present in form fields when specified in field list')
        self.assert_('id' not in form.base_fields,
            'id field is not present in form fields when not specified in field list')

        self.assert_('child' in form.subforms,
            'child field is present in subforms when specified in nested field list')
        self.assert_('val' in form.subforms['child'].base_fields,
            'val field present in child subform fields when specified in nested field list')
        self.assert_('id2' not in form.subforms['child'].base_fields,
            'id2 field is not present in child subform fields when not specified in nested field list')

        # form field order should match order in fields list
        self.assertEqual(form.base_fields.keys(), ['int', 'bool'])

        # second variant to confirm field order
        myfields = ['longtext', 'int', 'bool']
        myform = xmlobjectform_factory(TestObject, fields=myfields)
        form = myform()
        self.assertEqual(myfields, form.base_fields.keys())

    def test_exclude(self):
        # if exclude is specified, those fields should not be listed
        myform = xmlobjectform_factory(TestObject,
            exclude=['id', 'bool', 'child.id2'])
        form = myform()
        self.assert_('int' in form.base_fields,
            'int field is present in form fields when not excluded')
        self.assert_('longtext' in form.base_fields,
            'longtext field is present in form fields when not excluded')
        self.assert_('bool' not in form.base_fields,
            'bool field is not present in form fields when excluded')
        self.assert_('id' not in form.base_fields,
            'id field is not present in form fields when excluded')
        self.assert_('child' in form.subforms,
            'child subform is present in form fields when subfields excluded')
        self.assert_('val' in form.subforms['child'].base_fields,
            'val field is present in child subform fields when not excluded')
        self.assert_('id2' not in form.subforms['child'].base_fields,
            'id2 field is not present in child subform fields when excluded')

        # another variant for excluding an entire subform
        myform = xmlobjectform_factory(TestObject,
            exclude=['child'])
        form = myform()
        self.assert_('child' not in form.subforms,
            'child subform is not present in form fields when excluded')

    def test_widgets(self):
        # specify custom widget
        class MyForm(XmlObjectForm):
            class Meta:
                model = TestObject
                widgets = {'longtext': forms.Textarea }

        form = MyForm()
        self.assert_(isinstance(form.base_fields['longtext'].widget, forms.Textarea),
            'longtext form field has Textarea widget as specfied in form class Meta')
        self.assert_(isinstance(form.base_fields['id'].widget, forms.TextInput),
            'StringField id form field has default TextInput widget')

    def test_default_field_order(self):
        # form field order should correspond to field order in xmlobject, which is:
        # id, int, bool, longtext, [child]
        field_names = self.update_form.base_fields.keys()
        self.assertEqual('id', field_names[0],
            "first field in xmlobject ('id') is first in form fields")
        self.assertEqual('int', field_names[1],
            "second field in xmlobject ('int') is second in form fields")
        self.assertEqual('bool', field_names[2],
            "third field in xmlobject ('bool') is third in form fields")
        self.assertEqual('longtext', field_names[3],
            "fourth field in xmlobject ('longtext') is fourth in form fields")

        class MyTestObject(xmlmap.XmlObject):
            ROOT_NAME = 'foo'
            a = xmlmap.StringField('a')
            z = xmlmap.StringField('z')
            b = xmlmap.StringField('b')
            y = xmlmap.StringField('y')

        myform = xmlobjectform_factory(MyTestObject)
        form = myform()
        field_names = form.base_fields.keys()
        self.assertEqual('a', field_names[0],
            "first field in xmlobject ('a') is first in form fields")
        self.assertEqual('z', field_names[1],
            "second field in xmlobject ('z') is second in form fields")
        self.assertEqual('b', field_names[2],
            "third field in xmlobject ('b') is third in form fields")
        self.assertEqual('y', field_names[3],
            "fourth field in xmlobject ('y') is fourth in form fields")

        # what happens to order on an xmlobject with inheritance?

    def test_update_instance(self):
        # initialize data the same way a view processing a POST would
        update_form = TestForm(self.post_data, instance=self.testobj)
        # check that form is valid - if no errors, this populates cleaned_data
        self.assertTrue(update_form.is_valid())

        instance = update_form.update_instance()
        self.assert_(isinstance(instance, TestObject))
        self.assertEqual(21, instance.int)
        self.assertEqual(False, instance.bool)
        self.assertEqual('b', instance.id)
        self.assertEqual('completely new text content', instance.longtext)
        self.assertEqual(0, instance.other_child.val)
        
        # spot check that values were set properly in the xml
        xml = instance.serialize()
        self.assert_('id="b"' in xml)
        self.assert_('<boolean>no</boolean>' in xml)

        # test save on form with no pre-existing xmlobject instance
        class SimpleForm(XmlObjectForm):
            class Meta:
                model = TestObject
                fields = ['id', 'bool', 'longtext'] # fields with simple, top-level xpaths
                # creation for nested node not yet supported in xmlmap - excluding int
                exclude = ['child']      # exclude subform to simplify testing

        new_form = SimpleForm({'id': 'A1', 'bool': True, 'longtext': 'la-di-dah'})
        self.assertTrue(new_form.is_valid())
        instance = new_form.update_instance()
        self.assert_(isinstance(instance, TestObject),
            "update_instance on unbound xmlobjectform returns correct xmlobject instance")
        self.assertEqual(True, instance.bool)
        self.assertEqual('A1', instance.id)
        self.assertEqual('la-di-dah', instance.longtext)
        # spot check values in created-from-scratch xml
        xml = instance.serialize()
        self.assert_('id="A1"' in xml)
        self.assert_('<boolean>yes</boolean>' in xml)

        # formset deletion
        data = self.post_data.copy()
        # update post data to test deleting items
        data.update({
            'children-INITIAL_FORMS': 4,        # only initial forms can be deleted
            'children-0-DELETE': True,
            'children-2-DELETE': True,
        })
        # make a copy object, since the instance will be updated by the form
        testobj = xmlmap.load_xmlobject_from_string(self.testobj.serialize(), TestObject)
        update_form = TestForm(data, instance=self.testobj)
        # check that form is valid - if no errors, this populates cleaned_data
        self.assertTrue(update_form.is_valid())
        instance = update_form.update_instance()
        # children 0 and 2 should be removed from the updated instance
        self.assert_(testobj.children[0] not in instance.children)
        self.assert_(testobj.children[2] not in instance.children)

    def test_unsupported_fields(self):
        # xmlmap fields that XmlObjectForm doesn't know how to convert into form fields
        # should raise an exception

        class DateObject(xmlmap.XmlObject):
            ROOT_NAME = 'foo'
            date = DateTimeField('date')

        self.assertRaises(Exception, xmlobjectform_factory, DateObject)

    def test_subforms(self):
        # nodefields should be created as subforms on the object
        subform = self.new_form.subforms['child']
        self.assert_(isinstance(subform, XmlObjectForm),
            'form has an XmlObjectForm subform')

        expected, got = 'TestSubobjectXmlObjectForm', subform.__class__.__name__
        self.assertEqual(expected, got,
            "autogenerated subform class name: expected %s, got %s" % \
                (expected, got))
        self.assertEqual(TestSubobject, subform.Meta.model,
            "xmlobject class 'TestSubobject' correctly set as model in subform class Meta")
        expected, got = 'child', subform.prefix
        self.assertEqual(expected, got,
            "subform prefix is set to the name of the corresponding nodefield; expected %s, got %s" \
                % (expected, got))
        # subform fields - uses same logic tested above, so doesn't need thorough testing here
        self.assert_('val' in subform.base_fields, 'val field is present in subform fields')
        self.assert_('id2' in subform.base_fields, 'int field is present in subform fields')

        # required setting from xmlobject field
        self.assertFalse(subform.base_fields['val'].required,
            'form field generated from xmlobject field with required=False is not required')

        # subform is initialized with appropriate instance data
        subform = self.update_form.subforms['child']
        # initial values from subobject portion of test fixture
        expected, got = 'forty-two', subform.initial['id2']
        self.assertEqual(expected, got,
            "initial instance-based form value for 'id2' should be %s, got %s" % \
            (expected, got))
        # check rendered field for initial value
        self.assert_('value="%s"' % expected in str(subform['id2']),
            'rendered subform field has correct initial value')
        expected, got = 42, subform.initial['val']
        self.assertEqual(expected, got,
            "initial instance-based form value for 'val' should be %s, got %s" % \
            (expected, got))
        self.assert_('value="%s"' % expected in str(subform['val']),
            'rendered subform field has correct initial value')

        # subform label
        expected_val = 'Child bar1'
        self.assertEqual(expected_val, subform.form_label,
            'subform form_label should be set from xmlobject field verbose_name; ' +
            'expected %s, got %s' % (expected_val, subform.form_label))

        # test with prefixes
        update_form = TestForm(instance=self.testobj, prefix='pre')
        subform = update_form.subforms['child']
        expected, got = 'forty-two', subform.initial['id2']
        self.assertEqual(expected, got,
            "initial instance-based subform value for 'id2' should be %s, got %s" % \
            (expected, got))
        self.assert_('value="%s"' % expected in str(subform['id2']),
            'rendered subform field has correct initial value')
        expected, got = 42, subform.initial['val']
        self.assertEqual(expected, got,
            "initial instance-based form value for 'val' should be %s, got %s" % \
            (expected, got))
        self.assert_('value="%s"' % expected in str(subform['val']),
            'rendered subform field has correct initial value')

        # initialize with request data to test subform validation / instance update
        update_form = TestForm(self.post_data, instance=self.testobj)
        subform = update_form.subforms['child']
        self.assertTrue(update_form.is_valid()) 
        # nodefield instance should be set by main form update
        instance = update_form.update_instance()        
        self.assertEqual(2, instance.child.val)
        self.assertEqual('two', instance.child.id2)

    def test_formsets(self):
        # nodelistfields should be created as formsets on the object
        formset = self.new_form.formsets['children']
        self.assert_(isinstance(formset, BaseFormSet),
            'nodelist form has a BaseFormSet formset')
        self.assertEqual('TestSubobjectXmlObjectFormFormSet', formset.__class__.__name__)
        # StringListFields should be handled via formset
        str_formset = self.new_form.formsets['text']
        self.assert_(isinstance(str_formset, BaseXmlObjectListFieldFormSet),
            'stringlist formset is an instance of BaseXmlObjectListFieldFormset')
        # IntegerListFields should be handled via formset
        int_formset = self.new_form.formsets['numbers']
        self.assert_(isinstance(int_formset, BaseXmlObjectListFieldFormSet),
            'integerlist formset is an instance of BaseXmlObjectListFieldFormset')
    
        # formset label
        self.assertEqual('Children', formset.form_label,
            'formset form_label should be set based on xmlobject field name; ' +
            'excpected Children, got %s' % formset.form_label)
        self.assertEqual('Text', str_formset.form_label,
            'formset form_label should be set based on xmlobject field name; ' +
                         'excpected Text, got %s' % str_formset.form_label)
        self.assertEqual('Numbers', int_formset.form_label,
            'formset form_label should be set based on xmlobject field name; ' +
                         'excpected Text, got %s' % int_formset.form_label)

        subform = formset.forms[0]
        self.assert_(isinstance(subform, XmlObjectForm),
            'formset forms are XmlObjectForms')
        self.assertEqual('TestSubobjectXmlObjectForm', subform.__class__.__name__)
        self.assertEqual('children-0', subform.prefix)

        str_subform = str_formset.forms[0]
        self.assert_(isinstance(str_subform, ListFieldForm),
            'stringfield formset forms should be instances of ListFieldForm')
        
        int_subform = int_formset.forms[0]
        self.assert_(isinstance(int_subform, IntegerListFieldForm),
            'integerfield formset forms shoudl be instances of IntegerListFieldForm')

        # subform fields
        self.assert_('val' in subform.base_fields,
            'val field is present in subform fields')
        self.assert_('id2' in subform.base_fields,
            'id2 field is present in subform fields')        

        # initialize with an instance and verify initial values
        formset = self.update_form.formsets['children']
        self.assertEqual('forty-two', formset.forms[0].initial['id2'])
        self.assertEqual(42, formset.forms[0].initial['val'])
        self.assertEqual(None, formset.forms[1].initial['id2'])
        self.assertEqual(13, formset.forms[1].initial['val'])
         # check rendered fields for initial values
        self.assert_('value="forty-two"' in str(formset.forms[0]['id2']),
            'rendered formset field has correct initial value')
        self.assert_('value="42"' in str(formset.forms[0]['val']),
            'rendered formset field has correct initial value')
        self.assert_('value=""' not in str(formset.forms[1]['id2']),
            'rendered formset field has correct initial value')
        self.assert_('value="13"' in str(formset.forms[1]['val']),
            'rendered formset field has correct initial value')
        # - stringlist field
        str_formset = self.update_form.formsets['text']
        self.assertEqual('la', str_formset.forms[0].initial['val'])
        self.assertEqual('fa', str_formset.forms[1].initial['val'])

        # initialize with prefix
        update_form = TestForm(instance=self.testobj, prefix='pre')
        formset = update_form.formsets['children']
        self.assertEqual('forty-two', formset.forms[0].initial['id2'])
        self.assertEqual(42, formset.forms[0].initial['val'])
        self.assertEqual(None, formset.forms[1].initial['id2'])
        self.assertEqual(13, formset.forms[1].initial['val'])
        self.assert_('value="forty-two"' in str(formset.forms[0]['id2']),
            'rendered formset field has correct initial value')
        self.assert_('value="42"' in str(formset.forms[0]['val']),
            'rendered formset field has correct initial value')
        self.assert_('value=""' not in str(formset.forms[1]['id2']),
            'rendered formset field has correct initial value')
        self.assert_('value="13"' in str(formset.forms[1]['val']),
            'rendered formset field has correct initial value')

        # initialize with an instance and form data
        update_form = TestForm(self.post_data, instance=self.testobj)
        formset = update_form.formsets['children']
        self.assertTrue(update_form.is_valid())
        self.assertTrue(formset.is_valid())
        instance = update_form.update_instance()
        self.assertEqual(4, len(instance.children))
        self.assertEqual('two', instance.children[0].id2)
        self.assertEqual(2, instance.children[0].val)
        self.assertEqual('twenty-one', instance.children[1].id2)
        self.assertEqual(21, instance.children[1].val)
        self.assertEqual('five', instance.children[2].id2)
        self.assertEqual(5, instance.children[2].val)
        self.assertEqual('four', instance.children[3].id2)
        self.assertEqual(20, instance.children[3].val)
        # stringlistfield
        str_formset = update_form.formsets['text']
        self.assertTrue(str_formset.is_valid())
        self.assertEqual(['foo'], instance.text)        

    def test_can_order(self):
        class MySubFormset(XmlObjectForm):
            class Meta:
                model = TestSubobject
                can_order = True
        class OrderedTestForm(XmlObjectForm):
            children = SubformField(formclass=MySubFormset)
            class Meta:
                model = TestObject
                
        # test init option - currently only Meta.can_order works
        form = OrderedTestForm()
        self.assertTrue(form.formsets['children'].can_order)
        
        post_data = self.post_data.copy()
        post_data.update({
            'children-0-ORDER': 3,
            'children-1-ORDER': 2,
            'children-2-ORDER': 1
        })
        # the values should be orderd by ORDER value, not form order
        expected_order = [post_data['children-2-val'],
                             post_data['children-1-val'],
                             post_data['children-0-val']]
        update_form = OrderedTestForm(post_data, instance=self.testobj)
        self.assertTrue(update_form.is_valid())
        instance = update_form.update_instance()
        value_order = [ch.val for ch in instance.children]
        
        for i in range(3):
            self.assertEqual(expected_order[i], value_order[i])

    def test_is_valid(self):
        # missing required fields for main form but not subform or formsets
        form = TestForm({'int': 21, 'child-id2': 'two', 'child-val': 2,
                         'children-TOTAL_FORMS': 5, 'children-INITIAL_FORMS': 2,
                         'text-TOTAL_FORMS': 0, 'text-INITIAL_FORMS': 0,
                         'numbers-TOTAL_FORMS': 0, 'numbers-INITIAL_FORMS': 0 })
        self.assertFalse(form.is_valid(),
            "form is not valid when required top-level fields are missing")

        # no subform fields but have formsets
        form = TestForm({'int': 21, 'bool': True, 'id': 'b', 'longtext': 'short',
                         'children-TOTAL_FORMS': 5, 'children-INITIAL_FORMS': 2,
                         'text-TOTAL_FORMS': 0, 'text-INITIAL_FORMS': 0,
                         'numbers-TOTAL_FORMS': 0, 'numbers-INITIAL_FORMS': 0})
        self.assertFalse(form.is_valid(),
            "form is not valid when required subform fields are missing")

        form = TestForm(self.post_data, instance=self.testobj)
        # NOTE: passing in object instance because validation now attempts to initialize,
        # and dynamic creation of nodes like bar[2]/baz is currently not supported
        self.assertTrue(form.is_valid(),
            "form is valid when top-level and subform required fields are present")


    def test_valid_lazy_schema(self):
        with patch('eulxml.xmlmap.core.loadSchema') as mockloadschema:
            mockloadschema.side_effect = Exception
            # set a test XSD so xmlobject will attempt to load it
            self.testobj.XSD_SCHEMA = 'foo'
            # exception should be raised on init, not validation
            self.assertRaises(Exception, TestForm,
                              self.post_data, instance=self.testobj)
            

    def test_not_required(self):
        class MyForm(TestForm):
            id = forms.CharField(label='my id', required=False)

        data = self.post_data.copy()
        data['id'] = ''
        form = MyForm(data)
        self.assertTrue(form.is_valid(),
            'form is valid when non-required override field is empty')
        instance = form.update_instance()
        # empty string should actually remove node frome the xml
        self.assertEqual(None, instance.id)
        self.assertEqual(0, instance.node.xpath('count(@id)'))

    def test_override_subform(self):
        class MySubForm(XmlObjectForm):
            id2 = forms.URLField(label="my id")
            class Meta:
                model = TestSubobject

        subform_label = 'TEST ME'

        class MyForm(TestForm):
            child = SubformField(formclass=MySubForm, label=subform_label)
            class Meta:
                model = TestObject
                fields = ['id', 'int', 'child']
                
        form = MyForm()
        self.assert_(isinstance(form.subforms['child'], MySubForm),
            "child subform should be instance of MySubForm, got %s instead" % \
            form.subforms['child'].__class__)
        self.assertEqual('my id', form.subforms['child'].fields['id2'].label)        
        self.assert_('TEST ME' not in str(form),
                "subform pseudo-field should not appear in form output")
        
        # subform label - subformfield label should supercede field-based label
        self.assertEqual(subform_label, form.subforms['child'].form_label,
            'subform generated by SubformField form_label should be set by subform label; ' + \
            'expected %s, got %s' % (subform_label, form.subforms['child'].form_label))


    def test_override_formset(self):
        class MySubForm(XmlObjectForm):
            id2 = forms.URLField(label="my id")
            class Meta:
                model = TestSubobject

        class MyForm(TestForm):
            children = SubformField(formclass=MySubForm, label="TEST ME")

        form = MyForm()
        self.assert_(isinstance(form.formsets['children'].forms[0], MySubForm),
            "children formset form should be instance of MySubForm, got %s instead" % \
            form.formsets['children'].forms[0].__class__)
        self.assertEqual('my id', form.formsets['children'].forms[0].fields['id2'].label)
        self.assert_('TEST ME' not in str(form),
                "subform pseudo-field should not appear in form output")

    def test_override_subform_formset(self):
        # test nested override - a subform with a formset
        class MyTestSubObj(TestSubobject):
            parts = xmlmap.NodeListField('parts', TestSubobject)
            
        class MySubFormset(XmlObjectForm):
            uri = forms.URLField(label='uri')
            class Meta:
                model = MyTestSubObj

        class MySubForm(XmlObjectForm):
            parts = SubformField(formclass=MySubFormset)
            class Meta:
                model = MyTestSubObj
            
        class MyTestObj(TestObject):
            child = xmlmap.NodeField('bar[1]', MyTestSubObj)

        class MyForm(TestForm):
            child = SubformField(formclass=MySubForm, label="TEST ME")
            class Meta:
                model = MyTestObj

        form = MyForm()
        subformset = form.subforms['child'].formsets['parts'].forms[0]
        self.assert_(isinstance(subformset, MySubFormset))



if __name__ == '__main__':
    main()
