# file eulxml/forms/xmlobject.py
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

# xmlobject-backed django form (analogous to django db model forms)
# this code borrows heavily from django.forms.models

from collections import defaultdict
from string import capwords

from django.forms import BaseForm, CharField, IntegerField, BooleanField, \
        ChoiceField, Field, Form
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.forms import get_declared_fields
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import ModelFormOptions
from django.utils.datastructures  import SortedDict
from django.utils.safestring  import mark_safe

from eulxml import xmlmap

def fieldname_to_label(name):
    """Default conversion from xmlmap Field variable name to Form field label:
    convert '_' to ' ' and capitalize words.  Should only be used when verbose_name
    is not set."""
    return capwords(name.replace('_', ' '))


def _parse_field_list(fieldnames, include_parents=False):
    """
    Parse a list of field names, possibly including dot-separated subform
    fields, into an internal ParsedFieldList object representing the base
    fields and subform listed.
    
    :param fieldnames: a list of field names as strings. dot-separated names
        are interpreted as subform fields.
    :param include_parents: optional boolean, defaults to False. if True,
        subform fields implicitly include their parent fields in the parsed
        list.
    """
    field_parts = (name.split('.') for name in fieldnames)
    return _collect_fields(field_parts, include_parents)

def _collect_fields(field_parts_list, include_parents):
    """utility function to enable recursion in _parse_field_list()"""
    fields = []
    subpart_lists = defaultdict(list)

    for parts in field_parts_list:
        field, subparts = parts[0], parts[1:]
        if subparts:
            if include_parents and field not in fields:
                fields.append(field)
            subpart_lists[field].append(subparts)
        else:
            fields.append(field)

    subfields = dict((field, _collect_fields(subparts, include_parents))
                     for field, subparts in subpart_lists.iteritems())

    return ParsedFieldList(fields, subfields)

class ParsedFieldList(object):
    """A parsed list of fields, used internally by :class:`XmlObjectForm`
    for tracking field and exclude lists."""
    def __init__(self, fields, subfields):
        self.fields = fields
        self.subfields = subfields
        
class SubformAwareModelFormOptions(ModelFormOptions):
    """A :class:`~django.forms.models.ModelFormOptions` subclass aware of
    fields and exclude lists, parsing them for later reference by
    :class:`XmlObjectForm` internals."""

    def __init__(self, options=None):
        super(SubformAwareModelFormOptions, self).__init__(options)
        
        # store maximum number of repeated subforms that should be allowed
        self.max_num = getattr(options, 'max_num', None)
        self.can_delete = getattr(options, 'can_delete', True)
        self.can_order = getattr(options, 'can_order', False)
        self.extra = getattr(options, 'extra', 1)
        
        self.parsed_fields = None
        if isinstance(self.fields, ParsedFieldList):
            self.parsed_fields = self.fields
        elif self.fields is not None:
            self.parsed_fields = _parse_field_list(self.fields, include_parents=True)

        self.parsed_exclude = None
        if isinstance(self.exclude, ParsedFieldList):
            self.parsed_exclude = self.exclude
        elif self.exclude is not None:
            self.parsed_exclude = _parse_field_list(self.exclude, include_parents=False)



def formfields_for_xmlobject(model, fields=None, exclude=None, widgets=None, options=None,
        declared_subforms=None, max_num=None, extra=None):
    """
    Returns three sorted dictionaries (:class:`django.utils.datastructures.SortedDict`).
     * The first is a dictionary of form fields based on the
       :class:`~eulxml.xmlmap.XmlObject` class fields and their types.
     * The second is a sorted dictionary of subform classes for any fields of type
       :class:`~eulxml.xmlmap.fields.NodeField` on the model.
     * The third is a sorted dictionary of formsets for any fields of type
       :class:`~eulxml.xmlmap.fields.NodeListField` on the model.

    Default sorting (within each dictionary) is by XmlObject field creation order.

    Used by :class:`XmlObjectFormType` to set up a new :class:`XmlObjectForm`
    class.

    :param fields: optional list of field names; if specified, only the named fields
                will be returned, in the specified order
    :param exclude: optional list of field names that should not be included on
                the form; if a field is listed in both ``fields`` and ``exclude``,
                it will be excluded
    :param widgets: optional dictionary of widget options to be passed to form
                field constructor, keyed on field name
    :param options: optional :class:`~django.forms.models.ModelFormOptions`.
                if specified then fields, exclude, and widgets will default
                to its values.
    :param declared_subforms: optional dictionary of field names and form classes;
                if specified, the specified form class will be used to initialize
                the corresponding subform (for a :class:`~eulxml.xmlmap.fields.NodeField`)
                or a formset (for a :class:`~eulxml.xmlmap.fields.NodeListField`)
    :param max_num: optional value for the maximum number of times a fieldset should repeat.
    :param max_num: optional value for the number of extra forms to provide.
    """

    # first collect fields and excludes for the form and all subforms. base
    # these on the specified options object unless overridden in args.
    fieldlist = getattr(options, 'parsed_fields', None)
    if isinstance(fields, ParsedFieldList):
        fieldlist = fields
    elif fields is not None:
        fieldlist = _parse_field_list(fields, include_parents=True)

    excludelist = getattr(options, 'parsed_exclude', None)
    if isinstance(fields, ParsedFieldList):
        fieldlist = fields
    elif exclude is not None:
        excludelist = _parse_field_list(exclude, include_parents=False)

    if widgets is None and options is not None:
        widgets = options.widgets
        
    if max_num is None and options is not None:
        max_num = options.max_num

    # collect the fields (unordered for now) that we're going to be returning
    formfields = {}
    subforms = {}
    formsets = {}
    field_order = {}
    subform_labels = {}

    for name, field in model._fields.iteritems():  
        if fieldlist and not name in fieldlist.fields:
            # if specific fields have been requested and this is not one of them, skip it
            continue
        if excludelist and name in excludelist.fields:
            # if exclude has been specified and this field is listed, skip it
            continue
        if widgets and name in widgets:
            # if a widget has been specified for this field, pass as option to form field init
            kwargs = {'widget': widgets[name] }
        else:
            kwargs = {}
        # get apppropriate form widget based on xmlmap field type
        field_type = None

        # if the xmlmap field knows whether or not it is required, use for form
        if field.required is not None:
            kwargs['required'] = field.required
        if field.verbose_name is not None:
            kwargs['label'] = field.verbose_name
        if field.help_text is not None:
            kwargs['help_text'] = field.help_text
            
        if hasattr(field, 'choices') and field.choices:
            # if a field has choices defined, use a choice field (no matter what base type)
            field_type = ChoiceField
            kwargs['choices'] = [(val, val) for val in field.choices]
            # FIXME: how to properly do non-required choice field?
            # if field is optional, add a blank choice at the beginning of the list
            if field.required == False and '' not in field.choices:
                # TODO: add an empty_label option (like django ModelChoiceField)
                # to xmlobjectform and pass it in to make this easier to customize
                kwargs['choices'].insert(0, ('', ''))
        elif isinstance(field, xmlmap.fields.StringField):
            field_type = CharField
        elif isinstance(field, xmlmap.fields.IntegerField):
            field_type = IntegerField
        elif isinstance(field, xmlmap.fields.SimpleBooleanField):
            # by default, fields are required - for a boolean, required means it must be checked
            # since that seems nonsensical and not useful for a boolean,
            # setting required to False to allow True or False values
            kwargs['required'] = False
            field_type = BooleanField
            
        # datefield ? - not yet well-supported; leaving out for now        
        # ... should probably distinguish between date and datetime field
        
        elif isinstance(field, xmlmap.fields.NodeField) or \
            isinstance(field, xmlmap.fields.NodeListField):
            form_label = kwargs['label'] if 'label' in kwargs else fieldname_to_label(name)
            # store subform label in case we can't set on subform/formset
            subform_labels[name] = form_label
            
             # if a subform class was declared, use that class exactly as is
            if name in declared_subforms:
            	subform = declared_subforms[name]

            # otherwise, define a new xmlobject form for the nodefield or
            # nodelistfield class, using any options passed in for fields under this one
            else:              
                subform_opts = {
                    'fields': fieldlist.subfields[name] if fieldlist and name in fieldlist.subfields else None,
                    'exclude': excludelist.subfields[name] if excludelist and name in excludelist.subfields else None,
                    'widgets': widgets[name] if widgets and name in widgets else None,
                    'label': form_label,
                }

                # create the subform class
                subform = xmlobjectform_factory(field.node_class, **subform_opts)
            
            # store subform or generate and store formset, depending on field type
            if isinstance(field, xmlmap.fields.NodeField):
                subforms[name] = subform
            elif isinstance(field, xmlmap.fields.NodeListField):
                # formset_factory is from django core and we link into it here.
                formsets[name] = formset_factory(subform, formset=BaseXmlObjectFormSet,
                    max_num=subform._meta.max_num, can_delete=subform._meta.can_delete,
                    extra=subform._meta.extra, can_order=subform._meta.can_order)

                formsets[name].form_label = form_label

        elif isinstance(field, xmlmap.fields.StringListField) or \
	    isinstance(field, xmlmap.fields.IntegerListField):
            form_label = kwargs['label'] if 'label' in kwargs else fieldname_to_label(name)

            if isinstance(field, xmlmap.fields.IntegerListField):
            	listform = IntegerListFieldForm
            else:
            	listform = ListFieldForm

            # generate a listfield formset
            formsets[name] = formset_factory(listform, formset=BaseXmlObjectListFieldFormSet)
            # don't need can_delete: since each form is a single field, empty implies delete
            # todo: extra, max_num ? widget?
            formsets[name].form_label = form_label

        # TODO: other list variants


        else:
            # raise exception for unsupported fields
            # currently doesn't handle list fields
            raise Exception('Error on field "%s": XmlObjectForm does not yet support auto form field generation for %s.' \
            	% (name, field.__class__))

        if field_type is not None:
            if 'label' not in kwargs:
                kwargs['label'] = fieldname_to_label(name)
            formfields[name] = field_type(**kwargs)
            
        # create a dictionary indexed by field creation order, for default field ordering
        field_order[field.creation_counter] = name

    # if fields were explicitly specified, return them in that order
    if fieldlist:
        ordered_fields = SortedDict((name, formfields[name])
                                    for name in fieldlist.fields
                                    if name in formfields)
        ordered_subforms = SortedDict((name, subforms[name])
                                      for name in fieldlist.fields
                                      if name in subforms)
        ordered_formsets = SortedDict((name, formsets[name])
                                      for name in fieldlist.fields
                                      if name in formsets)
    else:
        # sort on field creation counter and generate a django sorted dictionary
        ordered_fields = SortedDict(
            [(field_order[key], formfields[field_order[key]]) for key in sorted(field_order.keys())
                                                if field_order[key] in formfields ]
        )
        ordered_subforms = SortedDict(
            [(field_order[key], subforms[field_order[key]]) for key in sorted(field_order.keys())
                                                if field_order[key] in subforms ]
        )
        ordered_formsets = SortedDict(
            [(field_order[key], formsets[field_order[key]]) for key in sorted(field_order.keys())
                                                if field_order[key] in formsets ]
        )
    return ordered_fields, ordered_subforms, ordered_formsets, subform_labels


def xmlobject_to_dict(instance, fields=None, exclude=None, prefix=''):
    """
    Generate a dictionary based on the data in an XmlObject instance to pass as
    a Form's ``initial`` keyword argument.

    :param instance: instance of :class:`~eulxml.xmlmap.XmlObject`
    :param fields: optional list of fields - if specified, only the named fields
            will be included in the data returned
    :param exclude: optional list of fields to exclude from the data
    """
    data = {}
    # convert prefix to combining form for convenience
    if prefix:
        prefix = '%s-' % prefix
    else:
        prefix = ''

    for name, field in instance._fields.iteritems():
        # not editable?
        if fields and not name in fields:
            continue
        if exclude and name in exclude:
            continue
        if isinstance(field, xmlmap.fields.NodeField):
            nodefield = getattr(instance, name)
            if nodefield is not None:
                subprefix = '%s%s' % (prefix, name)
                node_data = xmlobject_to_dict(nodefield, prefix=subprefix)
                data.update(node_data)   # FIXME: fields/exclude
        if isinstance(field, xmlmap.fields.NodeListField):
            for i, child in enumerate(getattr(instance, name)):
                subprefix = '%s%s-%d' % (prefix, name, i)
                node_data = xmlobject_to_dict(child, prefix=subprefix)
                data.update(node_data)   # FIXME: fields/exclude
        else:
            data[prefix + name] = getattr(instance, name)

    return data

class XmlObjectFormType(type):
    """
    Metaclass for :class:`XmlObject`.

    Analogous to, and substantially based on, Django's ``ModelFormMetaclass``.

    Initializes the XmlObjectForm based on the :class:`~eulxml.xmlmap.XmlObject`
    instance associated as a model. Adds form fields for supported
    :class:`~eulxml.xmlmap.fields.Field`s and 'subform' XmlObjectForm classes
    for any :class:`~eulxml.xmlmap.fields.NodeField` to the Form object.
    """
    def __new__(cls, name, bases, attrs):
        # let django do all the work of finding declared/inherited fields
        tmp_fields = get_declared_fields(bases, attrs, with_base_fields=False)
        declared_fields = {}
        declared_subforms = {}
        declared_subform_labels = {}
        # sort declared fields into sub-form overrides and regular fields
        for fname, f in tmp_fields.iteritems():
            if isinstance(f, SubformField):
                # FIXME: pass can_delete, can_delete from subformfield to formset? 
                declared_subforms[fname] = f.formclass
                # if a declared subform fields has a label specified, store it
                if hasattr(f, 'form_label') and f.form_label is not None:
                    declared_subform_labels[fname] = f.form_label
                # if a subformclass has a label, use that
                elif hasattr(f.formclass, 'form_label') and \
                         f.formclass.form_label is not None:
                    declared_subform_labels[fname] = f.formclass.form_label
            else:
                declared_fields[fname] = f

        new_class = super(XmlObjectFormType, cls).__new__(cls, name, bases, attrs)

        # use django's default model form options for fields, exclude, widgets, etc.
        opts = new_class._meta =  SubformAwareModelFormOptions(getattr(new_class, 'Meta',  None))
        if opts.model:
            # if a model is defined, get xml fields and any subform classes
            fields, subforms, formsets, subform_labels = formfields_for_xmlobject(opts.model, options=opts,
                    declared_subforms=declared_subforms)

            # Override default model fields with any custom declared ones
            # (plus, include all the other declared fields).
            fields.update(declared_fields)

            # store all of the dynamically generated xmlobjectforms for nodefields
            new_class.subforms = subforms

            # and for listfields
            new_class.formsets = formsets

            # labels for subforms that couldn't be set by formfields_for_xmlobject
            # declared subform labels should supercede verbose xmlobject field names
            subform_labels.update(declared_subform_labels)
            new_class.subform_labels = subform_labels

        else:
            fields = declared_fields
            new_class.subforms = {}
            new_class.formsets = {}

        new_class.declared_fields = declared_fields
        new_class.base_fields = fields

        return new_class


class XmlObjectForm(BaseForm):
    """Django Form based on an :class:`~eulxml.xmlmap.XmlObject` model,
    analogous to Django's ModelForm.

    Note that not all :mod:`eulxml.xmlmap.fields` are currently supported; all
    released field types are supported in their single-node variety, but no list
    field types are currently supported.  Attempting to define an XmlObjectForm
    without excluding unsupported fields will result in an Exception.

    Unlike Django's ModelForm, which provides a save() method, XmlObjectForm
    provides analogous functionality via :meth:`update_instance`.  Since an
    XmlObject by itself does not have a save method, and can only be saved
    in particular contexts, there is no general way for an XmlObjectForm to
    save an associated model instance to the appropriate datastore.

    If you wish to customize the html display for an XmlObjectForm, rather than
    using the built-in form display functions, be aware that if your XmlObject
    has any fields of type :class:`~eulxml.xmlmap.fields.NodeField`, you should
    make sure to display the subforms for those fields.

    NOTE: If your XmlObject includes NodeField elements and you do not want
    empty elements in your XML output when empty values are entered into the form,
    you may wish to extend :meth:`eulxml.xmlmap.XmlObject.is_empty` to correctly
    identify when your NodeField elements should be considered empty (if the
    default definition is not accurate or appropriate).  Empty elements will not
    be added to the :class:`eulxml.xmlmap.XmlObject` instance returned by
    :meth:`update_instance`.
    """

    # django has a basemodelform with all the logic
    # and then a modelform with the metaclass declaration; do we need that?
    __metaclass__ = XmlObjectFormType

    _html_section = None    # formatting for outputting object with subform

    subforms = {}
    """Sorted Dictionary of :class:`XmlObjectForm` instances for fields of type
    :class:`~eulxml.xmlmap.fields.NodeField` belonging to this Form's
    :class:`~eulxml.xmlmap.XmlObject` model, keyed on field name.  Ordered by
    field creation order or by specified fields."""
    
    form_label = None
    '''Label for this form or subform (set automatically for subforms &
    formsets, using the same logic that is used for field labels.'''

    def __init__(self, data=None, instance=None, prefix=None, initial={}, **kwargs):
        opts = self._meta
        # make a copy of any initial data for local use, since it may get updated with instance data
        local_initial = initial.copy()

        if instance is None:
            if opts.model is None:
                raise ValueError('XmlObjectForm has no XmlObject model class specified')
            # if we didn't get an instance, instantiate a new one
            # NOTE: if this is a subform, the data won't go anywhere useful
            # currently requires that instantiate_on_get param be set to True for NodeFields
            self.instance = opts.model()
            # track adding new instance instead of updating existing?
        else:
            self.instance = instance
            # generate dictionary of initial data based on current instance
            # allow initial data from instance to co-exist with other initial data
            local_initial.update(xmlobject_to_dict(self.instance)) #, prefix=prefix))  # fields, exclude?
            # FIXME: is this backwards? should initial data override data from instance?


        # In case XmlObject has a schema associated, make sure the
        # schema is accessible on load, so any schema-unavailability
        # on lazy-loaded schemas is discovered *before* form
        # submission & validation.
        self.instance.xmlschema

        # initialize subforms for all nodefields that belong to the xmlobject model
        self._init_subforms(data, prefix)
        self._init_formsets(data, prefix)
            
        super_init = super(XmlObjectForm, self).__init__
        super_init(data=data, prefix=prefix, initial=local_initial, **kwargs)
        # other kwargs accepted by XmlObjectForm.__init__:
        #    files, auto_id, object_data,
        #    error_class, label_suffix, empty_permitted

    def _init_subforms(self, data=None, prefix=None):
        # initialize each subform class with the appropriate model instance and data
        self.subforms = SortedDict()    # create as sorted dictionary to preserve order
        for name, subform in self.__class__.subforms.iteritems():
            # instantiate the new form with the current field as instance, if available
            if self.instance is not None:
                # get the relevant instance for the current NodeField variable
                # NOTE: calling create_foo will create the nodefield for element foo
                # creating here so subfields will be set correctly
                # if the resulting field is empty, it will be removed by update_instance
                getattr(self.instance, 'create_' + name)()
                subinstance = getattr(self.instance, name, None)
            else:
                subinstance = None
    
            if prefix:
                subprefix = '%s-%s' % (prefix, name)
            else:
                subprefix = name

            # instantiate the subform class with field data and model instance
            # - setting prefix based on field name, to distinguish similarly named fields
            newform = subform(data=data, instance=subinstance, prefix=subprefix)
            # depending on how the subform was declared, it may not have a label yet
            if newform.form_label is None:
                if name in self.subform_labels:
                    newform.form_label = self.subform_labels[name]

            self.subforms[name] = newform

    def _init_formsets(self, data=None, prefix=None):
        self.formsets = {}
        for name, formset in self.__class__.formsets.iteritems():
            if self.instance is not None:
                subinstances = getattr(self.instance, name, None)
            else:
                subinstances = None

            if prefix is not None:
                subprefix = '%s-%s' % (prefix, name)
            else:
                subprefix = name

            self.formsets[name] = formset(data=data, instances=subinstances, prefix=subprefix)

    def update_instance(self):
        """Save bound form data into the XmlObject model instance and return the
        updated instance."""

        # NOTE: django model form has a save method - not applicable here,
        # since an XmlObject by itself is not expected to have a save method
        # (only likely to be saved in context of a fedora or exist object)

        if hasattr(self, 'cleaned_data'):   # possible to have an empty object/no data

            opts = self._meta
            for name in self.instance._fields.iterkeys():
                if opts.fields and name not in opts.parsed_fields.fields:
                    continue
                if opts.exclude and name in opts.parsed_exclude.fields:
                    continue
                if name in self.cleaned_data:
                    # special case: we don't want empty attributes and elements
                    # for fields which returned no data from the form
                    # converting '' to None and letting XmlObject handle
                    if self.cleaned_data[name] == '':
                        self.cleaned_data[name] = None
                    setattr(self.instance, name, self.cleaned_data[name])

            # update sub-model portions via any subforms
            for name, subform in self.subforms.iteritems():
                self._update_subinstance(name, subform)
            for formset in self.formsets.itervalues():
                formset.update_instance()
        return self.instance

    def _update_subinstance(self, name, subform):
        """Save bound data for a single subform into the XmlObject model
        instance."""
        old_subinstance = getattr(self.instance, name)
        new_subinstance = subform.update_instance()

        # if our instance previously had no node for the subform AND the
        # updated one has data, then attach the new node.
        if old_subinstance is None and not new_subinstance.is_empty():
            setattr(self.instance, name, new_subinstance)

        # on the other hand, if the instance previously had a node for the
        # subform AND the updated one is empty, then remove the node.
        if old_subinstance is not None and new_subinstance.is_empty():
            delattr(self.instance, name)
    
    def is_valid(self):
        """Returns True if this form and all subforms (if any) are valid.
        
        If all standard form-validation tests pass, uses :class:`~eulxml.xmlmap.XmlObject`
        validation methods to check for schema-validity (if a schema is associated)
        and reporting errors.  Additonal notes:
        
         * schema validation requires that the :class:`~eulxml.xmlmap.XmlObject`
           be initialized with the cleaned form data, so if normal validation
           checks pass, the associated :class:`~eulxml.xmlmap.XmlObject` instance
           will be updated with data via :meth:`update_instance`
         * schema validation errors SHOULD NOT happen in a production system

        :rtype: boolean
        """
        valid = super(XmlObjectForm, self).is_valid() and \
                all(s.is_valid() for s in self.subforms.itervalues()) and \
                all(s.is_valid() for s in self.formsets.itervalues())
        # schema validation can only be done after regular validation passes,
        # because xmlobject must be updated with cleaned_data
        if valid and self.instance is not None:
            # update instance required to check schema-validity
            instance = self.update_instance()     
            if instance.is_valid():
                return True
            else:
                # if not schema-valid, add validation errors to error dictionary
                # NOTE: not overriding _get_errors because that is used by the built-in validation
                # append to any existing non-field errors
                if NON_FIELD_ERRORS not in self._errors:
                    self._errors[NON_FIELD_ERRORS] = self.error_class()
                self._errors[NON_FIELD_ERRORS].append("There was an unexpected schema validation error.  " +
                    "This should not happen!  Please report the following errors:")
                for err in instance.validation_errors():
                    self._errors[NON_FIELD_ERRORS].append('VALIDATION ERROR: %s' % err.message)
                return False
        return valid

    # NOTE: errors only returned for the *current* form, not for all subforms
    # - appears to be used only for form output, so this should be sensible

    def _html_output(self, normal_row, error_row, row_ender,  help_text_html, errors_on_separate_row):
        """Extend BaseForm's helper function for outputting HTML. Used by as_table(), as_ul(), as_p().
        
        Combines the HTML version of the main form's fields with the HTML content
        for any subforms.
        """
        parts = []
        parts.append(super(XmlObjectForm, self)._html_output(normal_row, error_row, row_ender,
                help_text_html, errors_on_separate_row))

        def _subform_output(subform):
            return subform._html_output(normal_row, error_row, row_ender,
                                        help_text_html, errors_on_separate_row)

        for name, subform in self.subforms.iteritems():
            # use form label if one was set
            if hasattr(subform, 'form_label'):
                name = subform.form_label
            parts.append(self._html_subform_output(subform, name, _subform_output))
        
        for name, formset in self.formsets.iteritems():
            parts.append(unicode(formset.management_form))
            # use form label if one was set
            # - use declared subform label if any
            if hasattr(formset.forms[0], 'form_label') and \
                    formset.forms[0].form_label is not None:
                 name = formset.forms[0].form_label
            # fallback to generated label from field name
            elif hasattr(formset, 'form_label'):
                name = formset.form_label

            # collect the html output for all the forms in the formset
            subform_parts = list()
                
            for subform in formset.forms:
                subform_parts.append(self._html_subform_output(subform,
                                      gen_html=_subform_output, suppress_section=True))
            # then wrap all forms in the section container, so formset label appears once
            parts.append(self._html_subform_output(name=name, content=u'\n'.join(subform_parts)))

        return mark_safe(u'\n'.join(parts))

    def _html_subform_output(self, subform=None, name=None, gen_html=None, content=None,
                             suppress_section=False):
        
        # pass the configured html section to subform in case of any sub-subforms
        if subform is not None:
            subform._html_section = self._html_section
            if gen_html is not None:
                content = gen_html(subform)
                
        # if html section is configured, add section label and wrapper for
        if self._html_section is not None and not suppress_section:
            return self._html_section % \
                {'label': fieldname_to_label(name), 'content': content}               
        else:
            return content
        

    # intercept the three standard html output formats to set an appropriate section format
    def as_table(self):
        """Behaves exactly the same as Django Form's as_table() method,
        except that it also includes the fields for any associated subforms
        in table format.

        Subforms, if any, will be grouped in a <tbody> labeled with a heading
        based on the label of the field.
        """
        self._html_section = u'<tbody><tr><th colspan="2" class="section">%(label)s</th></tr><tr><td colspan="2"><table class="subform">\n%(content)s</table></td></tr></tbody>'
        #self._html_section = u'<tbody><tr><th class="section" colspan="2">%(label)s</th></tr>\n%(content)s</tbody>'
        return super(XmlObjectForm, self).as_table()

    def as_p(self):
        """Behaves exactly the same as Django Form's as_p() method,
        except that it also includes the fields for any associated subforms
        in paragraph format.

        Subforms, if any, will be grouped in a <div> of class 'subform',
        with a heading based on the label of the field.
        """
        self._html_section = u'<div class="subform"><p class="label">%(label)s</p>%(content)s</div>'
        return super(XmlObjectForm, self).as_p()

    def as_ul(self):
        """Behaves exactly the same as Django Form's as_ul() method,
        except that it also includes the fields for any associated subforms
        in list format.

        Subforms, if any, will be grouped in a <ul> of class 'subform',
        with a heading based on the label of the field.
        """
        self._html_section = u'<li class="subform"><p class="label">%(label)s</p><ul>%(content)s</ul></li>'
        return super(XmlObjectForm, self).as_ul()


def xmlobjectform_factory(model, form=XmlObjectForm, fields=None, exclude=None,
                          widgets=None, max_num=None, label=None, can_delete=True,
                          extra=None, can_order=False):
    """Dynamically generate a new :class:`XmlObjectForm` class using the
    specified :class:`eulxml.xmlmap.XmlObject` class.
    
    Based on django's modelform_factory.
    """

    attrs = {'model': model}
    if fields is not None:
        attrs['fields'] = fields
    if exclude is not None:
        attrs['exclude'] = exclude
    if widgets is not None:
        attrs['widgets'] = widgets
    if max_num is not None:
        attrs['max_num'] = max_num
    if extra is not None:
        attrs['extra'] = extra
    if can_delete is not None:
        attrs['can_delete'] = can_delete
    if can_order is not None:
        attrs['can_order'] = can_order
        
    # If parent form class already has an inner Meta, the Meta we're
    # creating needs to inherit from the parent's inner meta.
    parent = (object,)
    if hasattr(form, 'Meta'):
        parent = (form.Meta, object)
    Meta = type('Meta', parent, attrs)

    # Give this new form class a reasonable name.
    class_name = model.__name__ + 'XmlObjectForm'

    # Class attributes for the new form class.
    form_class_attrs = {
        'Meta': Meta,
        # django has a callback formfield here; do we need that?
        # label for a subform/formset
        'form_label': label,
    }

    return XmlObjectFormType(class_name, (form,), form_class_attrs)

class BaseXmlObjectFormSet(BaseFormSet):
    def __init__(self, instances, **kwargs):
        self.instances = instances
        if 'initial' not in kwargs:
            kwargs['initial'] = [ xmlobject_to_dict(instance) for instance in instances ]
        super_init = super(BaseXmlObjectFormSet, self).__init__
        super_init(**kwargs)

    def _construct_form(self, i, **kwargs):
        try:
            defaults = { 'instance': self.instances[i] }
        except:
            defaults = {}
        defaults.update(kwargs)

        super_construct = super(BaseXmlObjectFormSet, self)._construct_form
        return super_construct(i, **defaults)

    def update_instance(self):
        for form in getattr(self, 'deleted_forms', []):
            # update_instance may be called multiple times - instance can only
            # be removed the first time, so don't consider it an error if it's not present
            if form.instance in self.instances:
                self.instances.remove(form.instance)

        # if forms can be ordered, remove existing records and re-add
        # in the appropriate order so that any changes in order are
        # reflected in the xml
        if self.can_order:
            for form in self.ordered_forms:
                if form.instance in self.instances:
                    self.instances.remove(form.instance)
                form.update_instance()
                self.instances.append(form.instance)

        else:
            for form in self.initial_forms:
                if form.has_changed():
                    form.update_instance()
            for form in self.extra_forms:
                if form.has_changed():
                    form.update_instance()
                    self.instances.append(form.instance)

    # NOTE: when displaying forms that use formsets to the user, it is recommended
    # to re-initialize the form after a successful update before re-displaying it
    # so that the formset forms (initial, deleted, extra) will be re-initialized
    # based on the latest data & display correctly

class SubformField(Field):
    """This is a pseudo-form field: use to override the form class of a subform or
    formset that belongs to an :class:`XmlObjectForm`.

    Note that if you specify a list of fields, the subform or formset needs to
    be included in that list or it will not be displayed when the form is generated.

    Example usage::

        class MyFormPart(XmlObjectForm):
            id = StringField(label='my id', required=False)
            ...

        class MyForm(XmlObjectForm):
            part = SubformField(formclass=MyFormPart)
            ...

    In this example, the subform ``part`` on an instance of **MyForm** will be
    created as an instance of **MyFormPart**.
    """
    def __init__(self, formclass=None, label=None, can_delete=True, can_order=False,
                 *args, **kwargs):
        if formclass is not None:
            self.formclass = formclass
        if label is not None:
            self.form_label = label
        self.can_delete = can_delete
        self.can_order = can_order
        
        # may not need to actually call init since we don't really use this as a field
        super(SubformField, self).__init__(*args, **kwargs)


class ListFieldForm(Form):
    'Basic, single-input form to use for non-nodelist xmlmap list field formsets'
    val = CharField(label='', required=False)
    # suppress field label (should be labeled as a formset only), make not required
    # - empty field means an item should be removed from the list

    def __init__(self, instance=None, *args, **kwargs):
        # populate initial value: convert list instance data to form field data
        if instance is not None:
            kwargs['initial'] = {'val': instance }
        super(ListFieldForm, self).__init__(*args, **kwargs)

    @property
    def value(self):
        # convenience property to access the value of the one field input
        # - expects to be used on a bound form
        cleaned_data = self.clean()
        if 'val' in cleaned_data:
            return cleaned_data['val']

class IntegerListFieldForm(ListFieldForm):
    'Extend :class:`ListFieldForm` and set input field to be an IntegerField'
    val = IntegerField(label='', required=False)

class BaseXmlObjectListFieldFormSet(BaseFormSet):
    'Formset class for non-node-based xmlmap list fields (e.g., string & integer list fields)'
    def __init__(self, instances, **kwargs):
        # store listfield instance for initializing forms and updating
        self.instance = instances
        super(BaseXmlObjectListFieldFormSet, self).__init__(**kwargs)

    def initial_form_count(self):
        # initial form count is based on number of entries in the instance list
        return len(self.instance)

    def _construct_form(self, i, **kwargs):
        # initialize forms, passing in the appropriate initial data from the instance list
        try:
            defaults = {'instance': self.instance[i] }
        except:
            defaults = {}
        defaults.update(kwargs)
            
        return super(BaseXmlObjectListFieldFormSet, self)._construct_form(i, **defaults)

    def update_instance(self):
        # construct the complete list of values (one value per form)
        values = [form.value for form in self.forms if form.value]

        # replace current list contents with new values
        while len(self.instance):
            self.instance.pop()
        self.instance.extend(values)

