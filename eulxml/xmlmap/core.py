# file eulxml/xmlmap/core.py
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

import cStringIO
import logging
import os
import urllib2
import warnings

from lxml import etree
from lxml.builder import ElementMaker

from eulxml.xmlmap.fields import Field, NodeList

logger = logging.getLogger(__name__)

__all__ = [ 'XmlObject', 'parseUri', 'parseString', 'loadSchema',
    'load_xmlobject_from_string', 'load_xmlobject_from_file' ]

# NB: When parsing XML in this module, we explicitly create a new parser
#   each time. Without this, lxml 2.2.7 uses a global default parser. When
#   parsing strings, lxml appears to set that parser into no-network mode,
#   causing subsequent network-based parses to fail. Specifically, under
#   lxml 2.2.7, the second call here fails::
#
#   >>> etree.fromstring('<foo/>') # set global parser to no-network
#   >>> etree.parse('http://www.w3.org/2001/xml.xsd') # fails in no-network mode
#
#   If we simply construct a separate parser each time, parses will be
#   marginally slower, but this lxml bug will not affect us.
#
#   This lxml behavior has been logged as a bug:
#   https://bugs.launchpad.net/lxml/+bug/673205

def parseUri(stream, uri=None):
    """Read an XML document from a URI, and return a :mod:`lxml.etree`
    document."""
    return etree.parse(stream, parser=_get_xmlparser(), base_url=uri)
def parseString(string, uri=None):
    """Read an XML document provided as a byte string, and return a
    :mod:`lxml.etree` document. String cannot be a Unicode string.
    Base_uri should be provided for the calculation of relative URIs."""
    return etree.fromstring(string, parser=_get_xmlparser(), base_url=uri)

# internal cache for loaded schemas, so we only load each schema once
_loaded_schemas = {}
def loadSchema(uri, base_uri=None, override_proxy_requirement=False):
    """Load an XSD XML document (specified by filename or URL), and return a
    :class:`lxml.etree.XMLSchema`.
    
    Note that frequently loading a schema without using a web proxy may
    introduce significant network resource usage as well as instability if
    the schema becomes unavailable. Thus this function will fail if the
    ``HTTP_PROXY`` environment variable is not set.
    """

    # uri to use for reporting errors - include base uri if any
    if uri in _loaded_schemas:
        return _loaded_schemas[uri]
    
    error_uri = uri
    if base_uri is not None:
        error_uri += ' (base URI %s)' % base_uri

    # typical reliable use should include a proxy. warn if they're not using
    # one.
    if 'HTTP_PROXY' not in os.environ and _http_uri(uri):
        message = ('Loading schema %s without a web proxy may introduce ' +
                   'significant network resource usage as well as ' +
                   'instability if that server becomes inaccessible. ' + 
                   'The HTTP_PROXY environment variable is required ' +
                   'for loading schemas.  Schema validation will be disabled.') \
                  % (error_uri,)
        if override_proxy_requirement:
            message += (' (overridden: Requesting without proxy. Please ' +
                        'set HTTP_PROXY as soon as possible.)')
            logger.warning(message)
        else:
            warnings.warn(message, UserWarning)
            # bail out and return None instead of a schema, so methods
            # that rely on a loaded schema can detect its absence and
            # proceed accordingly.
            return None

    try:
        logger.debug('Loading schema %s' % uri)
        _loaded_schemas[uri] = etree.XMLSchema(etree.parse(uri,
                                                           parser=_get_xmlparser(),
                                                           base_url=base_uri))
        return _loaded_schemas[uri]
    except IOError as io_err:
        # add a little more detail to the error message - but should still be an IO error
        raise IOError('Failed to load schema %s : %s' % (error_uri, io_err))
    except etree.XMLSchemaParseError as parse_err:
        # re-raise as a schema parse error, but ensure includes details about schema being loaded
        raise etree.XMLSchemaParseError('Failed to parse schema %s -- %s' % (error_uri, parse_err))
def _http_uri(uri):
    return uri.startswith('http:') or uri.startswith('https:')

class _FieldDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return self.field.get_for_node(obj.node, obj.context)

    def __set__(self, obj, value):        
        return self.field.set_for_node(obj.node, obj.context, value)

    def __delete__(self, obj):
        return self.field.delete_for_node(obj.node, obj.context)


class XmlObjectType(type):

    """
    A metaclass for :class:`XmlObject`.

    Analogous in principle to Django's ``ModelBase``, this metaclass
    functions rather differently. While it'll likely get a lot closer over
    time, we just haven't been growing ours long enough to demand all of the
    abstractions built into Django's models. For now, we do three things:

      1. take any :class:`~eulxml.xmlmap.fields.Field` members and convert
         them to descriptors,
      2. store all of these fields and all of the base classes' fields in a
         ``_fields`` dictionary on the class, and
      3. if any local (non-parent) fields look like self-referential
         :class:`eulxml.xmlmap.NodeField` objects then patch them up
         to refer to the newly-created :class:`XmlObject`.

    """

    def __new__(cls, name, bases, defined_attrs):
        use_attrs = {}
        fields = {}
        recursive_fields = []

        # inherit base fields first; that way current class field defs will
        # override parents. note that since the parents already added fields
        # from *their* parents (because they were built from XmlObjectType),
        # we don't have to recurse.
        for base in bases:
            base_fields = getattr(base, '_fields', None)
            if base_fields:
                fields.update(base_fields)
            base_xsd = getattr(base, 'XSD_SCHEMA', None)

        schema_obj = None

        for attr_name, attr_val in defined_attrs.items():
            # XXX: not a fan of isintance here. maybe use something like
            # django's contribute_to_class?
            if isinstance(attr_val, Field):
                if isinstance(attr_val, SchemaField):
                    # special case: schema field will look at the schema and return appropriate field type
                    if 'XSD_SCHEMA' in defined_attrs or base_xsd:
                        # load schema_obj the first time we need it
                        if schema_obj is None:
                            # if xsd schema is directly defined, use that
                            if 'XSD_SCHEMA' in defined_attrs:
                                schema_obj = load_xmlobject_from_file(defined_attrs['XSD_SCHEMA'],
                                                                      XsdSchema)
                            # otherwise, use nearest parent xsd
                            else:
                                schema_obj = load_xmlobject_from_file(base_xsd, XsdSchema)
                        
                        attr_val = attr_val.get_field(schema_obj)
                field = attr_val
                fields[attr_name] = field
                use_attrs[attr_name] = _FieldDescriptor(field)

                # collect self-referential NodeFields so that we can resolve
                # them once we've created the new class
                node_class = getattr(field, 'node_class', None)
                if isinstance(node_class, basestring):
                    if node_class in ('self', name):
                        recursive_fields.append(field)
                    else:
                        msg = ('Class %s has field %s with node_class %s, ' +
                               'but the only supported class names are ' +
                               '"self" and %s.') % (name, attr_val,
                                                    repr(node_class),
                                                    repr(name))
                        raise ValueError(msg)

                # if a field 'foo' has a 'create_for_node' method, then add
                # a 'create_foo' method to call it. generally this isn't
                # helpful, but NodeField uses it.
                if hasattr(attr_val, 'create_for_node'):
                    create_method_name = 'create_' + attr_name
                    create_method = cls._make_create_field(create_method_name, attr_val)
                    use_attrs[create_method_name] = create_method

            else:
                use_attrs[attr_name] = attr_val
        use_attrs['_fields'] = fields

        super_new = super(XmlObjectType, cls).__new__
        new_class = super_new(cls, name, bases, use_attrs)

        # patch self-referential NodeFields (collected above) with the
        # newly-created class
        for field in recursive_fields:
            assert field.node_class in ('self', name)
            field.node_class = new_class

        return new_class

    @staticmethod
    def _make_create_field(field_name, field):
        def create_field(xmlobject):
            field.create_for_node(xmlobject.node, xmlobject.context)
        create_field.__name__ = field_name
        return create_field

class XmlObject(object):

    """
    A Python object wrapped around an XML node.

    Typical programs will define subclasses of :class:`XmlObject` with
    various field members. Some programs will use
    :func:`load_xmlobject_from_string` and :func:`load_xmlobject_from_file`
    to create instances of these subclasses. Other programs will create them
    directly, passing a node argument to the constructor. If the
    subclass defines a :attr:`ROOT_NAME` then this node argument is
    optional: Programs may then create instances directly with no
    constructor arguments.

    Programs can also pass an optional dictionary to the constructor to
    specify namespaces for XPath evaluation.

    If keyword arguments are passed in to the constructor, they will be used to
    set initial values for the corresponding fields on the :class:`XmlObject`.
    (Only currently supported for non-list fields.)

    Custom equality/non-equality tests: two instances of :class:`XmlObject` are
    considered equal if they point to the same lxml element node.
    """

    __metaclass__ = XmlObjectType

    node = None
    """The top-level xml node wrapped by the object"""

    ROOT_NAME = None
    """A default root element name (without namespace prefix) used when an object
    of this type is created from scratch."""
    ROOT_NS = None
    """The default namespace used when an object of this type is created from
    scratch."""
    ROOT_NAMESPACES = {}
    """A dictionary whose keys are namespace prefixes and whose values are
    namespace URIs. These namespaces are used to create the root element when an
    object of this type is created from scratch; should include the namespace
    and prefix for the root element, if it has one. Any additional namespaces
    will be added to the root element."""

    XSD_SCHEMA = None
    """URI or file path to the XSD schema associated with this :class:`XmlObject`,
    if any.  If configured, will be used for optional validation when calling
    :meth:`load_xmlobject_from_string` and :meth:`load_xmlobject_from_file`,
    and with :meth:`is_valid`.
    """

    schema_validate = True
    '''Override for schema validation; if a schema must be defined for
     the use of :class:`xmlmap.fields.SchemaField` for a sub-xmlobject
     that should not be validated, set to False.'''
    
    @property
    def xmlschema(self):
        """A parsed XSD schema instance of
        :class:`lxml.etree.XMLSchema`; will be loaded the first time
        it is requested on any instance of this class if XSD_SCHEMA is
        set and xmlchema is None.  If you wish to load and parse the
        schema at class definition time, instead of at class instance
        initialization time, you may want to define your schema in
        your subclass like this::
        
          XSD_SCHEMA = "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
          xmlschema = xmlmap.loadSchema(XSD_SCHEMA)
          
        """
        if self.XSD_SCHEMA:
            return loadSchema(self.XSD_SCHEMA)
    
    # NOTE: DTD and RNG validation could be handled similarly to XSD validation logic

    def __init__(self, node=None, context=None, **kwargs):
        if node is None:
            node = self._build_root_element()

        self.node = node
        # FIXME: context probably needs work
        # get namespaces from current node OR its parent (in case of an lxml 'smart' string)
        if hasattr(node, 'nsmap'):
            nsmap = node.nsmap
        elif hasattr(node, 'getParent'):
            nsmap = node.nsmap
        else:
            nsmap = {}

        # xpath has no notion of a default namespace - omit any namespace with no prefix
        self.context = {'namespaces': dict([(prefix, ns) for prefix, ns in nsmap.iteritems() if prefix ]) }

        if context is not None:
            self.context.update(context)
        if hasattr(self, 'ROOT_NAMESPACES'):
            # also include any root namespaces to guarantee that expected prefixes are available
            self.context['namespaces'].update(self.ROOT_NAMESPACES)

        for field, value in kwargs.iteritems():
            # TODO (maybe): handle setting/creating list fields
            setattr(self, field, value)

    def _build_root_element(self):
        opts = {}
        if hasattr(self, 'ROOT_NS'):
            opts['namespace'] = self.ROOT_NS
        if hasattr(self, 'ROOT_NAMESPACES'):
            opts['nsmap'] = self.ROOT_NAMESPACES

        E = ElementMaker(**opts)
        root = E(self.ROOT_NAME)
        return root
        

    def xsl_transform(self, filename=None, xsl=None, return_type=None, **params):
        """Run an xslt transform on the contents of the XmlObject.

        XSLT can be passed as filename or string. If a params dictionary is
        specified, its items will be passed as parameters to the XSL
        transformation.

        :param filename: xslt filename (optional, one of file and xsl is required)
        :param xsl: xslt as string (optional)
        :param return_type: type of object to return; optional, defaults to
            :class:`XmlObject`
        :returns: an instance of :class:`XmlObject` or the return_type specified
        """
        parser = _get_xmlparser()
        if filename is not None:
            xslt_doc = etree.parse(filename, parser=parser)
        if xsl is not None:
            xslt_doc = etree.fromstring(xsl, parser=parser)
        transform = etree.XSLT(xslt_doc, **params)
        # NOTE: converting _XSLTResultTree to XmlObject because of a bug in its unicode method
        # - to output xml result, use serialize instead of unicode
        if return_type is None:
            return_type = XmlObject
        return return_type(transform(self.node))

    def __unicode__(self):
        if isinstance(self.node, basestring):
            return self.node
        return self.node.xpath("normalize-space(.)")

    def __string__(self):
        if isinstance(self.node, basestring):
            return self.node
        return unicode(self).encode('ascii', 'xmlcharrefreplace')

    def __eq__(self, other):
        # consider two xmlobjects equal if they are pointing to the same xml node
        if hasattr(other, 'node') and self.node == other.node:
            return True
        # consider two xmlobjects equal if they serialize the same
        if hasattr(other, 'serialize') and self.serialize() == other.serialize():
            return True
        # NOTE: does not address "equivalent" xml, which is potentially very complex
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def serialize(self, stream=None, pretty=False):
        """Serialize the contents of the XmlObject to a stream.  Serializes
        current node only; for the entire XML document, use :meth:`serializeDocument`.

        If no stream is specified, returns a string.
        :param stream: stream or other file-like object to write content to (optional)
        :param pretty: pretty-print the XML output; boolean, defaults to False
        :rtype: stream passed in or an instance of :class:`cStringIO.StringIO`
        """
        return self._serialize(self.node, stream=stream, pretty=pretty)

    def serializeDocument(self, stream=None, pretty=False):
        """Serialize the contents of the entire XML document (including Doctype
        declaration, if there is one), with an XML declaration, for the current
        XmlObject to a stream.

        If no stream is specified, returns a string.
        :param stream: stream or other file-like object to write content to (optional)
        :param pretty: pretty-print the XML output; boolean, defaults to False
        :rtype: stream passed in or an instance of :class:`cStringIO.StringIO`
        """
        return self._serialize(self.node.getroottree(), stream=stream, pretty=pretty,
                                xml_declaration=True)

    def _serialize(self, node, stream=None, pretty=False, xml_declaration=False):
        # actual logic of xml serialization
        if stream is None:
            string_mode = True
            stream = cStringIO.StringIO()
        else:
            string_mode = False

        # NOTE: etree c14n doesn't seem to like fedora info: URIs
        stream.write(etree.tostring(node, encoding='UTF-8', pretty_print=pretty,
                                    xml_declaration=xml_declaration))

        if string_mode:
            data = stream.getvalue()
            stream.close()
            return data

        return stream

    def is_valid(self):
        """Determine if the current document is valid as far as we can determine.
        If there is a schema associated, check for schema validity.  Otherwise,
        return True.

        :rtype: boolean
        """
        # valid if there are no validation errors
        return self.validation_errors() == []

    def validation_errors(self):
        """Return a list of validation errors.  Returns an empty list
        if the xml is schema valid or no schema is defined.  If a
        schema is defined but :attr:`schema_validate` is False, schema
        validation will be skipped.
        
        Currently only supports schema validation.

        :rtype: list
        """
        # if we add other types of validation (DTD, RNG), incorporate them here
        if self.xmlschema and self.schema_validate and not self.schema_valid():
            return self.schema_validation_errors()
        return []

    def schema_valid(self):
        """Determine if the current document is schema-valid according to the
        configured XSD Schema associated with this instance of :class:`XmlObject`.

        :rtype: boolean
        :raises: Exception if no XSD schema is defined for this XmlObject instance
        """
        if self.xmlschema is not None:
            return self.xmlschema.validate(self.node)
        else:
            raise Exception('No XSD schema is defined, cannot validate document')

    def schema_validation_errors(self):
        """
        Retrieve any validation errors that occured during schema validation
        done via :meth:`is_valid`.
        
        :returns: a list of :class:`lxml.etree._LogEntry` instances
        :raises: Exception if no XSD schema is defined for this XmlObject instance
        """
        if self.xmlschema is not None:
            return self.xmlschema.error_log
        else:
            raise Exception('No XSD schema is defined, cannot return validation errors')

    def is_empty(self):
        """
        Returns True if the root node contains no child elements, no
        attributes, and no text. Returns False if any are present.
        """
        return len(self.node) == 0 and len(self.node.attrib) == 0 \
            and not self.node.text and not self.node.tail # regular text or text after a node

class Urllib2Resolver(etree.Resolver):
    def resolve(self, url, public_id, context):
        if url.startswith('/'):
            url = 'file:' + url

        logger.debug('Resolving url %s' % url)
        f = urllib2.urlopen(url, None, 10)
        # set a timeout in case connection fails or is unreasonably slow
        return self.resolve_file(f, context, base_url=url)
_defaultResolver = Urllib2Resolver()

def _get_xmlparser(xmlclass=XmlObject, validate=False, resolver=_defaultResolver):
    """Initialize an instance of :class:`lxml.etree.XMLParser` with appropriate
    settings for validation.  If validation is requested and the specified
    instance of :class:`XmlObject` has an XSD_SCHEMA defined, that will be used.
    Otherwise, uses DTD validation.
    """
    if validate:
        if hasattr(xmlclass, 'XSD_SCHEMA') and xmlclass.XSD_SCHEMA is not None:
            # If the schema has already been loaded, use that.
            # (since we accessing the *class*, accessing 'xmlschema' returns a property,
            # not the initialized schema object we actually want).
            xmlschema = getattr(xmlclass, '_xmlschema', None)
            # otherwise, load the schema
            if xmlschema is None:
                xmlschema = loadSchema(xmlclass.XSD_SCHEMA)
            opts = {'schema': xmlschema}
        else:
            # if configured XmlObject does not have a schema defined, assume DTD validation
            opts = {'dtd_validation': True}    
    else:
        # if validation is not requested, no parser options are needed
        opts = {}

    parser = etree.XMLParser(**opts)
    
    if resolver is not None:
        parser.resolvers.add(resolver)
        
    return parser

def load_xmlobject_from_string(string, xmlclass=XmlObject, validate=False,
        resolver=None):
    """Initialize an XmlObject from a string.

    If an xmlclass is specified, construct an instance of that class instead
    of :class:`~eulxml.xmlmap.XmlObject`. It should be a subclass of XmlObject.
    The constructor will be passed a single node.

    If validation is requested and the specified subclass of :class:`XmlObject`
    has an XSD_SCHEMA defined, the parser will be configured to validate against
    the specified schema.  Otherwise, the parser will be configured to use DTD
    validation, and expect a Doctype declaration in the xml content.

    :param string: xml content to be loaded, as a string
    :param xmlclass: subclass of :class:`~eulxml.xmlmap.XmlObject` to initialize
    :param validate: boolean, enable validation; defaults to false
    :rtype: instance of :class:`~eulxml.xmlmap.XmlObject` requested
    """
    parser = _get_xmlparser(xmlclass=xmlclass, validate=validate, resolver=resolver)    
    element = etree.fromstring(string, parser)
    return xmlclass(element)


def load_xmlobject_from_file(filename, xmlclass=XmlObject, validate=False,
        resolver=None):
    """Initialize an XmlObject from a file.

    See :meth:`load_xmlobject_from_string` for more details; behaves exactly the
    same, and accepts the same parameters, except that it takes a filename
    instead of a string.

    :param filename: name of the file that should be loaded as an xmlobject.
        :meth:`etree.lxml.parse` will accept a file name/path, a file object, a
        file-like object, or an HTTP or FTP url, however file path and URL are
        recommended, as they are generally faster for lxml to handle.    
    """
    parser = _get_xmlparser(xmlclass=xmlclass, validate=validate, resolver=resolver)

    tree = etree.parse(filename, parser)
    return xmlclass(tree.getroot())

# Import these for backward compatibility. Should consider deprecating these
# and asking new code to pull them from descriptor
from eulxml.xmlmap.fields import *

# XSD schema xmlobjects - used in XmlObjectType to process SchemaFields
# FIXME: where should these actually go? depends on both XmlObject and fields

class XsdType(XmlObject):
    ROOT_NAME = 'simpleType'
    name = StringField('@name')
    base = StringField('xs:restriction/@base')
    restricted_values = StringListField('xs:restriction/xs:enumeration/@value')

    def base_type(self):
        # for now, only supports simple types - eventually, may want logic to
        # traverse extended types to get to base XSD type
        if ':' in self.base:    # for now, ignore prefix (could be xsd, xs, etc. - how to know which?)
            prefix, basetype = self.base.split(':')
        else:
            basetype = self.base
        return basetype
    

class XsdSchema(XmlObject):
    ROOT_NAME = 'schema'
    ROOT_NS = 'http://www.w3.org/2001/XMLSchema'
    ROOT_NAMESPACES = {'xs': ROOT_NS }

    def get_type(self, name=None, xpath=None):
        if xpath is None:
            if name is None:
                raise Exception("Must specify either name or xpath")
            xpath = '//*[@name="%s"]' % name

        result = self.node.xpath(xpath)
        if len(result) == 0:
            raise Exception("No Schema type definition found for xpath '%s'" % xpath)
        elif len(result) > 1:
            raise Exception("Too many schema type definitions found for xpath '%s' (found %d)" \
                        % (xpath, len(result)))
        return XsdType(result[0], context=self.context) # pass in namespaces



