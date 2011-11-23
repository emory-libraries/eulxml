:mod:`eulxml.xmlmap` -- Map XML to Python objects
==================================================

.. module:: eulxml.xmlmap

:mod:`eulxml.xmlmap` makes it easier to map XML to Python objects. The
Python DOM does some of this, of course, but sometimes it's prettier to wrap
an XML node in a typed Python object and assign attributes on that object to
reference subnodes by `XPath <http://www.w3.org/TR/xpath/>`_ expressions.
This module provides that functionality.

:class:`XmlObject` Instances
----------------------------

.. toctree::
   :maxdepth: 1

   Encoded Archive Description (EAD) XmlObject <xmlmap/ead>
   Dublin Core XmlObject <xmlmap/dc>
   Collaborative Electronic Records Project (CERP) XmlObject <xmlmap/cerp>
   Metadata Object Description Schema (MODS) XmlObject <xmlmap/mods>
   Preservation Metadata Implementation Strategies (PREMIS) XmlObjects <xmlmap/premis>

General Usage
-------------

Suppose we have an XML object that looks something like this:

.. code-block:: xml

   <foo>
     <bar>
       <baz>42</baz>
     </bar>
     <bar>
       <baz>13</baz>
     </bar>
     <qux>A</qux>
     <qux>B</qux>
   </foo>

For this example, we want to access the value of the first ``<baz>`` as a
Python integer and the second ``<baz>`` as a string value. We also want to
access all of them (there may be lots on another ``<foo>``) as a big list of
integers. We can create an object to map these fields like this::

   from eulxml import xmlmap

   class Foo(xmlmap.XmlObject):
       first_baz = xmlmap.IntegerField('bar[1]/baz')
       second_baz = xmlmap.StringField('bar[2]/baz')
       qux = xmlmap.StringListField('qux')
   
:attr:`first_baz`, :attr:`second_baz`, and :attr:`all_baz` here are
attributes of the :class:`Foo` object. We can access them in later code like
this::

   >>> foo = xmlmap.load_xmlobject_from_file(foo_path, xmlclass=Foo)
   >>> foo.first_baz
   42
   >>> foo.second_baz
   '13'
   >>> foo.qux
   ['A', 'B']
   >>> foo.first_baz=5
   >>> foo.qux.append('C')
   >>> foo.qux[0] = 'Q'
   >>> print foo.serialize(pretty=True)
   <foo>
     <bar>
       <baz>5</baz>
     </bar>
     <bar>
       <baz>13</baz>
     </bar>
     <qux>Q</qux>
     <qux>B</qux>
   <qux>C</qux></foo>


Concepts
--------

:mod:`~eulxml.xmlmap` simplifies access to XML data in Python. Programs
can define new :class:`~eulxml.xmlmap.XmlObject` subclasses representing a
type of XML node with predictable structure. Members of these classes can be
regular methods and values like in regular Python classes, but they can also be
special :ref:`field <xmlmap-field>` objects that associate XPath expressions
with Python data elements. When code accesses these fields on the object, the
code evaluates the associated XPath expression and converts the data to a
Python value.

:class:`XmlObject`
------------------

Most programs will use :mod:`~eulxml.xmlmap` by defining a subclass of
:class:`XmlObject` containing :ref:`field <xmlmap-field>` members.

.. autoclass:: XmlObject([node[, context]])
    :members:

    .. attribute:: _fields

      A dictionary mapping field names to :ref:`field <xmlmap-field>`
      members. This dictionary includes all of the fields defined on the
      class as well as those inherited from its parents.
      

:class:`~eulxml.xmlmap.core.XmlObjectType`
-------------------------------------------

.. autoclass:: eulxml.xmlmap.core.XmlObjectType
    :members:


.. _xmlmap-field:


Field types
-----------

There are several predefined field types. All of them evaluate XPath
expressions and map the resultant XML nodes to Python types. They differ
primarily in how they map those XML nodes to Python objects as well as in
whether they expect their XPath expression to match a single XML node or a
whole collection of them.

Field objects are typically created as part of an :class:`XmlObject`
definition and accessed with standard Python object attribute syntax. If a
:class:`Foo` class defines a :attr:`bar` attribute as an
:mod:`~eulxml.xmlmap` field object, then an object will reference it simply
as ``foo.bar``.

.. automodule:: eulxml.xmlmap.fields
   :members:               


Other facilities
----------------

.. autofunction:: eulxml.xmlmap.load_xmlobject_from_string

.. autofunction:: eulxml.xmlmap.load_xmlobject_from_file

.. autofunction:: eulxml.xmlmap.parseString

.. autofunction:: eulxml.xmlmap.parseUri

.. autofunction:: eulxml.xmlmap.loadSchema(uri, base_uri=None)
